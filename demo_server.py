import argparse
import yaml
import pyaudio
import logging
import asyncio
import json
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk
from websockets.asyncio.server import serve

logging.basicConfig(filename="log.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

async def main(config_file):
    with open(config_file, 'r') as file:
        logging.info("Loading configuration")
        config = yaml.safe_load(file)
    
    conversation = [
        {
            "role": "system",
            "content": ""
        }
    ]
    
    connected_clients = []    
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
    audio_config = speechsdk.AudioConfig(use_default_microphone = True)
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config, audio_config=audio_config)
    
    def transcribing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        logging.info(f"Transcribing: Speaker {evt.result.speaker_id}: {evt.result.text}")

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
            response = {
                "action": "conversation",
                "conversation": conversation
            }
            for websocket in connected_clients:
                websocket.send(json.dumps(response))
            
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logging.error('NOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))

    conversation_transcriber.transcribing.connect(transcribing_cb)
    conversation_transcriber.transcribed.connect(transcribed_cb)

    logging.info("Start transcription")
    conversation_transcriber.start_transcribing_async().get()  # wait for voidfuture, so we know engine initialization is done.
    print('Continuous Recognition is now running, say something.')

    async def handler(websocket): 
        async for message in websocket:
            logging.info(f"Websocket Request: ${message}")
            print(f"<<< {message}")
            
            request = json.loads(message)
            if request["action"] == "assistant":
                message = {
                    "role": "assistant",
                    "content": ""
                }
                conversation.append(message)
                conversation_transcriber.stop_transcribing_async()
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=conversation,
                    stream=True
                )
                print('\x1b[1;33;42m ChatGPT:')
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        print(chunk.choices[0].delta.content, end="")
                        message["content"] += chunk.choices[0].delta.content
                print('\x1b[0m\n')
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
                conversation_transcriber.start_transcribing_async().get()
            elif request["action"] == "change":
                message = conversation[request["index"]]
                message["content"] = request["message"]
            elif request["action"] == "remove":
                message = conversation.remove(conversation["index"])
            elif request["action"] == "instructions":
                message = conversation[0]
                message["content"] = request["instructions"]
                
            response = {
                "action": "conversation",
                "conversation": conversation
            }
            await websocket.send(json.dumps(response))
        print("Closed connection")
    
    async with serve(handler, "127.0.0.1", 4000):
        await asyncio.get_running_loop().create_future()

if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    args = parser.parse_args()
    asyncio.run(main(args.config_file))
    