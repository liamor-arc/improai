import logging
import asyncio
from openai import AsyncOpenAI
from .EventHandler import EventHandler
import azure.cognitiveservices.speech as speechsdk

class OpenAIConversation:
    def __init__(self, config, client:AsyncOpenAI):
        self.transcribing = False
        self.generating = False
        self.config = config
        self.conversation = [
            {
                "role": "system",
                "content": ""
            }
        ] 
        self.chat_client = client
        logging.info("Loading Azure Speech Service")
        speech_config = speechsdk.SpeechConfig(
            subscription=self.config["azure-speech"]["api-key"],
            region=self.config["azure-speech"]["region"],
            speech_recognition_language="en-us"
        )
        speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, value='true')
        speech_config.set_property(property_id=speechsdk.PropertyId.Speech_LogFilename, value=".log/SpeechSDKLog.log")
        audio_config = speechsdk.AudioConfig(use_default_microphone = True)
        self.conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config, audio_config=audio_config)
        # Bug doesn't allow class method for transcribing
        self.conversation_transcriber.transcribing.connect(OpenAIConversation.transcribing)
        self.conversation_transcriber.transcribed.connect(self.transcribed)
        self.conversation_transcriber.canceled.connect(self.canceled)
        self.eventHandler = EventHandler()
    
    def run(self):
        self.conversation_transcriber.start_transcribing_async().get()
    
    def transcribing(evt: speechsdk.SpeechRecognitionEventArgs):
        logging.info(f"Transcribing: Speaker {evt.result.speaker_id}: {evt.result.text}")

    def transcribed(self, evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info(f"Transcribed: Speaker {evt.result.speaker_id}: {evt.result.text}")
            if not evt.result.text:
                return
            print(f'{evt.result.speaker_id}: {evt.result.text}')
            self.conversation.append({
                "role": "user",
                "name": evt.result.speaker_id,
                "content": evt.result.text
            })
            print("Emit transcribed")
            self.eventHandler.emit("transcribed")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logging.error('NOMATCH: Speech could not be TRANSCRIBED: {}'.format(evt.result.no_match_details))
       
    def canceled(self, evt: speechsdk.transcription.ConversationTranscriptionCanceledEventArgs):
        logging.info(f"Cancelled: {evt.cancellation_details}")
             
    def onTranscribed(self, callback):
        self.eventHandler.addEventHandler("transcribed", callback)
        
    def onAssistantGenerating(self, callback):
        self.eventHandler.addEventHandler("assistant_generating", callback)
        
    def onAssistantDone(self, callback):
        self.eventHandler.addEventHandler("assistant_done", callback)
    
    def command(self, request):
        if request["command"] == "Start Transcribing":
            self.transcribing = True
            self.conversation_transcriber.start_transcribing_async().get()
        elif request["command"] == "Stop Transcribing":
            self.transcribing = False
            self.conversation_transcriber.stop_transcribing_async()            
    
    def message(self, request):
        if request["action"] == "command":
            return self.command(request)
        elif request["action"] == "assistant":
            self.generate()
        elif request["action"] == "append":
            message = {
                "role": "user",
                "content": request["message"]
            }
            if request["name"]:
                message["name"] = request["name"]
            self.conversation.append(message)
            if request["generate"]:
                self.generate()
        elif request["action"] == "change":
            message = self.conversation[request["index"]]
            message["content"] = request["message"]
        elif request["action"] == "remove":
            self.conversation.remove(self.conversation[request["index"]])
        elif request["action"] == "instructions":
            message = self.conversation[0]
            message["content"] = request["instructions"]
    
    def generate(self):
        coroutine = self.generateAsync()
        try:
            asyncio.get_running_loop().create_task(coroutine)
        except:
            asyncio.run(coroutine)
        
    async def generateAsync(self):
        message = {
            "role": "assistant",
            "content": ""
        }
        self.generating = True
        prevTranscribing = self.transcribing
        if prevTranscribing:
            self.transcribing = False
            self.conversation_transcriber.stop_transcribing_async()
        stream = await self.chat_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.conversation,
            stream=True
        )
        self.conversation.append(message)
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                chunk_content = chunk.choices[0].delta.content
                self.eventHandler.emit("assistant_generating", chunk_content)
                message["content"] += chunk_content
                # await asyncio.sleep(0.1)
        print(f'\x1b[1;33;42m ChatGPT: {message["content"]}\x1b[0m\n')
        self.generating = False
        logging.info("Response ChatGPT: {}".format(message["content"]))
        self.eventHandler.emit("assistant_done", message["content"])
        if prevTranscribing:
            self.transcribing = True
            self.conversation_transcriber.start_transcribing_async().get()
        