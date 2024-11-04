import argparse
import yaml
import time
import pyaudio
import logging
import sys
import signal
import keyboard
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk

logging.basicConfig(filename="log.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def main(config_file, instruction_file):
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
        },
        {
            "role": "user",
            "content": ""
        }
    ]
    
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
        speech_recognition_language="nl-be"
    )
    audio_config = speechsdk.AudioConfig(use_default_microphone = True)
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config, audio_config=audio_config)
    
    def transcribing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        logging.info(f"Transcribing: {evt.result.text}")

    def transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info(f"Transcribed: {evt.result.text}")
            if not evt.result.text:
                return
            text = evt.result.text
            while text[0] in [".", ","]:
                text = text[1:]
            text = text.split(" ")[0].lower()
            if text[-1] in [".", ",", "?", "!", ";"]:
                text = text[0:-1]
            print(text + " ", end="")
            conversation[1]["content"] += text + " "
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logging.error('NOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))

    conversation_transcriber.transcribing.connect(transcribing_cb)
    conversation_transcriber.transcribed.connect(transcribed_cb)

    logging.info("Start transcription")
    conversation_transcriber.start_transcribing_async().get()  # wait for voidfuture, so we know engine initialization is done.
    print('Continuous Recognition is now running, say something.')

    def signal_handler(sig, frame):
        conversation_transcriber.stop_transcribing_async()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to quit the program')
    print('Press any key to have ChatGPT continue the sentence')
    while True:
        time.sleep(0.1)
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            logging.info("Sending conversation to ChatGPT")
            conversation_transcriber.stop_transcribing_async()
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                stream=True
            )
            response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content
            text = response
            while text[0] in [".", ","]:
                text = text[1:]
            text = text.split(" ")[0].lower()
            # if text[-1] in [".", ",", "?", "!", ";"]:
            #    text = text[0:-1]
            conversation[1]["content"] += text + " "
            print(f'\x1b[1;33;42m{text}\x1b[0m ', end="")
            logging.info("Response ChatGPT: {}".format(response))
            logging.info("Generating sound file with 'echo' voice and pcm")
            response = client.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=text,
                response_format="pcm"
            )
            audio = pyaudio.PyAudio()
            audio_stream = audio.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
            for audio_chunk in response.iter_bytes(chunk_size=1024):
                audio_stream.write(audio_chunk)
            audio_stream.stop_stream()
            conversation_transcriber.start_transcribing_async().get()

if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    parser.add_argument('--instructions_file', type=str, default="./instructions.yml", help='The location of the instructions file')
    args = parser.parse_args()
    main(args.config_file, args.instructions_file)