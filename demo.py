import argparse
import yaml
from openai import OpenAI

def main(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    client = OpenAI(
        api_key=config["openai"]["api-key"],
        organization=config["openai"]["organization-id"],
        project=config["openai"]["project-id"]
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say several paragraphs of random things."}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
        
if __name__ == '__main__':        
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default="./environment.yml", help='The location of the config file')
    args = parser.parse_args()
    main(args.config_file)