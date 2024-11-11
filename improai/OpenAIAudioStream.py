import pyaudio
import logging
import asyncio
from openai import AsyncOpenAI

class OpenAIAudioStream:
    def __init__(self, client:AsyncOpenAI):
        self.client = client
    
    def play(self, message):
        coroutine = self.playAsync(message)
        asyncio.create_task(coroutine)
            
    async def playAsync(self, message):
        logging.info("Generating sound file with 'echo' voice and pcm")
        response = await self.client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=message,
                response_format="pcm"
            )
        audio = pyaudio.PyAudio()
        audio_stream = audio.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
        async for audio_chunk in await response.aiter_bytes(chunk_size=1024):
            audio_stream.write(audio_chunk)
        audio_stream.stop_stream()