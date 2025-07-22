# TextToSpeech.py
import requests
import random
import asyncio
import os
import playsound
from rich import print

datafile=r"Fronted\File\chat.data"
# Default voice
AssistantVoice = "Aditi"
    
async def TextToAudioFile(text: str) -> None:
    """
    Asynchronously downloads TTS audio from StreamElements and saves to speech.mp3
    """
    file_path = r'Data/speech.mp3'

    if os.path.exists(file_path):
        os.remove(file_path)

    try:
        # Generate audio using StreamElements API
        url = f"https://api.streamelements.com/kappa/v2/speech?voice={AssistantVoice}&text={{{text}}}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(response.content)
        else:
            print("Error: Could not fetch TTS from StreamElements.")

    except Exception as e:
        msg="[red]There are Some Problem in My Voice.[/red]"
        print(msg)

def TTS(Text, func=lambda r=None: True):
    """
    Synchronously plays speech.mp3 after generating it.
    """
    try:
        asyncio.run(TextToAudioFile(Text))

        file_path = r'Data/speech.mp3'
        playsound.playsound(file_path)
        return True

    except Exception as e:
        print(f"Error in TTS: {e}")

    finally:
        try:
            func(False)
            if os.path.exists(r'Data/speech.mp3'):
                os.remove(r'Data/speech.mp3')
        except Exception as e:
            print(f"Error in finally block: {e}")

def TextToSpeech(Text, func=lambda r=None: True):
    """
    Smart TTS: speaks full or partial text based on length.
    """
    Data = str(Text).split("-")

    responses = [
        "Please check the chat screen for the remaining text.",
        "You can see more information on your screen now.",
        "Sir, the rest of the answer is available in the chat.",
        "Check the rest of the message on the screen, sir.",
        "You'll find more details in the chat window."
    ]

    if len(Data) > 4 and len(Text) >= 250:
        TTS(" ".join(Text.split(".")[0:2]) + ". " + random.choice(responses), func)
    else:
        TTS(Text, func)

if __name__ == "__main__":
    os.makedirs("Data", exist_ok=True)
    while True:
        TextToSpeech(input("Enter the Text: "))
