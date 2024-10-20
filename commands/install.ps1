python -m venv .venv

.\commands\environment.ps1

python -m pip install --upgrade pip

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install openai
pip install pyyaml
pip install azure-cognitiveservices-speech
pip install transformers sentencepiece datasets[audio]
pip install pyaudio

deactivate