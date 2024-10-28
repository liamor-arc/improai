import yaml
import argparse
import signal
import sys
import time
import azure.cognitiveservices.speech as speechsdk

def main(config_file):
    with open(config_file, 'r') as file:
        print("Loading configuration")
        config = yaml.safe_load(file)
        
    print("Loading Azure Speech Service")
    speech_config = speechsdk.SpeechConfig(
        subscription=config["azure-speech"]["api-key"],
        region=config["azure-speech"]["region"],
        speech_recognition_language="en-US"
    )
    speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, value='true')
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config)
    
    def transcribing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        print(f"Transcribing: Speaker {evt.result.speaker_id}: {evt.result.text}")

    def transcribed_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"Transcribed: Speaker {evt.result.speaker_id}: {evt.result.text}")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print('NOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))

    conversation_transcriber.transcribing.connect(transcribing_cb)
    conversation_transcriber.transcribed.connect(transcribed_cb)

    print("Start transcription")
    
    conversation_transcriber.start_transcribing_async().get()  # wait for voidfuture, so we know engine initialization is done.
    print('Continuous Recognition is now running, say something.')
    
    def signal_handler(sig, frame):
        conversation_transcriber.stop_transcribing_async()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to quit the program')
    
    while True:
        time.sleep(0.1)

if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    args = parser.parse_args()
    main(args.config_file)