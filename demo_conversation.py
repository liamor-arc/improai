import argparse
import yaml
import time
import pyaudio
import logging
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk

logging.basicConfig(filename="log.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def main(config_file, instruction_file, can_interrupt):
    with open(config_file, 'r') as file:
        logging.info("Loading configuration")
        config = yaml.safe_load(file)
        
    with open(instruction_file, 'r') as file:
        logging.info("Loading instructions")
        instructions = yaml.safe_load(file)
    
    conversation = [
        {
            "role": "system",
            "content": instructions["openai"]
        }
    ]
    latest_transcription = time.time()
    interrupted = False
    
    logging.info("Loading OpenAI client")
    client = OpenAI(
        api_key=config["openai"]["api-key"],
        organization=config["openai"]["organization-id"],
        project=config["openai"]["project-id"]
    )
    logging.info("Loading Azure Speech Service")
    speech_config = speechsdk.SpeechConfig(
        subscription=config["azure-speech"]["api-key"],
        region=config["azure-speech"]["region"],
        speech_recognition_language="en-US"
    )
    speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, value='true')
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config)
    
    def transcribing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        logging.info(f"Transcribing: Speaker {evt.result.speaker_id}: {evt.result.text}")
        nonlocal latest_transcription, interrupted
        latest_transcription = time.time()
        interrupted = can_interrupt and True

    def transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info(f"Transcribed: Speaker {evt.result.speaker_id}: {evt.result.text}")
            if not evt.result.text:
                return
            print(f'{evt.result.speaker_id}: {evt.result.text}')
            conversation.append({
                "role": "user",
                "name": evt.result.speaker_id,
                "content": evt.result.text
            })
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logging.error('NOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))

    conversation_transcriber.transcribing.connect(transcribing_cb)
    conversation_transcriber.transcribed.connect(transcribed_cb)

    logging.info("Start transcription")
    conversation_transcriber.start_transcribing_async().get()  # wait for voidfuture, so we know engine initialization is done.
    print('Continuous Recognition is now running, say something.')

    print('Press Ctrl-C to stop program')
    while True:
        time.sleep(0.1)
        if (conversation[-1]["role"] != "assistant" and time.time()-latest_transcription>1):
            logging.info("Sending conversation to ChatGPT")
            if not can_interrupt:
                conversation_transcriber.stop_transcribing_async()
            interrupted = False
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                stream=True
            )
            message = {
                "role": "assistant",
                "content": ""
            }
            conversation.append(message)
            for chunk in stream:
                # interrupt bot talking
                if interrupted:
                    logging.info("Response ChatGPT: {}".format(message["content"]))
                    logging.info("Bot interrupted")
                    break
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="")
                    message["content"] += chunk.choices[0].delta.content
            logging.info("Response ChatGPT: {}".format(message["content"]))
            logging.info("Generating sound file with 'echo' voice and pcm")
            response = client.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=message["content"],
                response_format="pcm"
            )
            audio = pyaudio.PyAudio()
            audio_stream = audio.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
            for audio_chunk in response.iter_bytes(chunk_size=1024):
                audio_stream.write(audio_chunk)
            audio_stream.stop_stream()
            if not can_interrupt:
                conversation_transcriber.start_transcribing_async().get()
            print("\n")

if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    parser.add_argument('--instructions_file', type=str, default="./instructions.yml", help='The location of the instructions file')
    parser.add_argument('--can_interrupt', action='store_true', help='Can ChatGPT be interrupted during speech?')
    args = parser.parse_args()
    main(args.config_file, args.instructions_file, args.can_interrupt)