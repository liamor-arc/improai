import argparse
import logging
import yaml
from openai import AsyncOpenAI
from improai.Logging import initializeLogging
from improai.OpenAIAudioStream import OpenAIAudioStream

def main(config_file, message):
    initializeLogging(".log/log.log")
    with open(config_file, 'r') as file:
        print("Loading configuration")
        config = yaml.safe_load(file)
    logging.info("Loading OpenAI client")
    client = AsyncOpenAI(
        api_key=config["openai"]["api-key"],
        organization=config["openai"]["organization-id"],
        project=config["openai"]["project-id"]
    )
    audio_stream = OpenAIAudioStream(client)
    audio_stream.play(message)

if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--message', type=str, required=True)
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    args = parser.parse_args()
    main(args.message)
    