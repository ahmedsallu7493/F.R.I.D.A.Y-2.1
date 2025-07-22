from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import subprocess
import requests
import keyboard
import asyncio
import os
from typing import List
from Backend.TextToSpeech import TextToSpeech as tx
# from movmentdetect import FingerMouseController

# Load environment variables once
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
client = Groq(api_key=GroqAPIKey)


useragent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/100.0.4896.75 Safari/537.36"
)


def GoogleSearch(Topic):
    # ser=Topic[7:]
    query = f"https://www.google.com/search?q={Topic}"
    tx(f"Alright, searching for {Topic} on Google.")
    webopen(query)
    tx(f"Done! I found some results for {Topic} on Google.")
    return True

def content(topic: str) -> bool:
    try:
        clean_topic = topic.replace("Content ", "").strip()
        tx(f"Getting things ready to write the content.")
        if not clean_topic:
            raise ValueError("Empty topic provided")

        filename = f"Data/Content/{clean_topic.lower().replace(' ', '_')}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        messages = [{"role": "user", "content": clean_topic}]
        completion = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=messages,
            max_tokens=2038,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        # Efficiently concatenate response
        content_text = "".join(
            chunk.choices[0].delta.content
            for chunk in completion
            if chunk.choices[0].delta.content
        )

        tx(f"The content has been written and Save successfully.")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content_text)

        subprocess.Popen(['notepad.exe', filename])
        return True

    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        msg="[red]Error: {e}[/red]"
        return False
    
def PlayYoutube(query):
    tx(f"Okay, just a moment. Playing {query} on YouTube.")
    playonyt(query)
    return True

def OpenApp(app, sess=requests.Session()):
    try:
        tx(f"Alright, opening {app} for you.")
        appopen(app, match_closest=True, output=True, throw_error=True)
        tx(f"The app has been opened successfully.")
        return True
    except:
        def search_google(query):
            try:
                response = sess.get(
                    f"https://www.google.com/search?q={query}",
                    headers={"User-Agent": useragent},
                    timeout=5
                )
                return response.text if response.status_code == 200 else None
            except requests.RequestException:
                return None

        def extract_links(html):
            if not html:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            return [link.get('href') for link in soup.find_all('a') if link.get('href')]

        html = search_google(app)
        links = extract_links(html)
        if links:
            webopen(links[0])
            return True
        return False

def CloseApp(app):
    try:
        tx(f"Ok Wait I am Closing the{app}")
        close(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False

def System(command):
    tx(f"Okay, give me a moment...")
    key_map = {
        "mute": 'volume mute',
        "unmute": 'volume mute',
        "volume up": 'volume up',
        "volume down": 'volume down'
    }
    if command in key_map:
        keyboard.press_and_release(key_map[command])
    return True

async def TranslateAndExecute(commands: List[str]):
    funcs = []
    for command in commands:
        cmd = command.lower()
        if cmd.startswith("open "):
            funcs.append(asyncio.to_thread(OpenApp, command[5:]))
        elif cmd.startswith("close "):
            funcs.append(asyncio.to_thread(CloseApp, command[6:]))
        elif cmd.startswith("play "):
            funcs.append(asyncio.to_thread(PlayYoutube, command[5:]))
        elif cmd.startswith("content "):
            funcs.append(asyncio.to_thread(content, command[8:]))
        elif cmd.startswith("google"):
            funcs.append(asyncio.to_thread(GoogleSearch, command[7:]))
            # GoogleSearch(command)
        elif cmd.startswith("system "):
            funcs.append(asyncio.to_thread(System, command[7:]))
        # elif cmd.startswith("control"):
        #     funcs.append(asyncio.to_thread(control))
        else:
            print(f"[yellow]No Function Found for:[/yellow] {command}")
            msg="[yellow]No Function Found for:[/yellow] {command}"

    return await asyncio.gather(*funcs)

async def Automation(commands: List[str]):
    return await TranslateAndExecute(commands)


# if __name__ == "__main__":
#     GoogleSearch("GTU")

