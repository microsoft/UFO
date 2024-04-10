import sys
import subprocess

subprocess.run(["pip", "install", "-r", "requirements.txt"])

# Check if "-option" is passed as an argument
if "-qwen" in sys.argv:
    subprocess.run(["pip", "install", "dashscope"])

if "-ollama" in sys.argv:
    subprocess.run(["curl", "https://ollama.ai/install.sh", "|", "sh"])
