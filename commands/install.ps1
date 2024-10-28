python -m venv .venv

.\commands\environment.ps1

python -m pip install --upgrade pip

# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

deactivate