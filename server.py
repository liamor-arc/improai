import argparse
import asyncio
import logging
import yaml
from openai import AsyncOpenAI
from improai.Logging import initializeLogging
from improai.WebSocket import WebSocket
from improai.OpenAIConversation import OpenAIConversation
from improai.OpenAIAudioStream import OpenAIAudioStream

async def main(config_file):
    initializeLogging(".log/log.log")
    async with WebSocket("127.0.0.1", 4000) as socket:
        with open(config_file, 'r') as file:
            print("Loading configuration")
            config = yaml.safe_load(file)
        logging.info("Loading OpenAI client")
        client = AsyncOpenAI(
            api_key=config["openai"]["api-key"],
            organization=config["openai"]["organization-id"],
            project=config["openai"]["project-id"]
        )
        conversation = OpenAIConversation(config, client)
        audio_stream = OpenAIAudioStream(client)
        def sync():
            print("sync")
            response = {
                "action": "conversation",
                "conversation": conversation.conversation,
                "transcribing": conversation.transcribing,
                "generating": conversation.generating
            }
            socket.sendToAll(response)
        def onJSON(request):
            if request["action"]=="play":
                audio_stream.play(request["message"])
                return
            conversation.message(request)
            sync()
        def onAssistantGenerating(chunk):
            sync()
        def onAssistantDone(message):
            sync()
            audio_stream.play(message)
        conversation.onTranscribed(sync)
        conversation.onAssistantGenerating(onAssistantGenerating)
        conversation.onAssistantDone(onAssistantDone)
        socket.onJSON(onJSON)
        await asyncio.get_running_loop().create_future()

if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    args = parser.parse_args()
    asyncio.run(main(args.config_file))
    