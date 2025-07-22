from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from deep_translator import GoogleTranslator
import os
from rich import print

datafile=r"Fronted\File\chat.data"
# Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-logging")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")

# Chrome driver setup
service = Service(ChromeDriverManager().install(), service_log_path=os.devnull)
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(r'F:/F.R.I.D.A.Y/Data/voice.html')

question_words = {"who", "what", "when", "where", "why", "how", "which", "whom", "whose"}

def speech_recognition(timeout=15):
    try:
        driver.find_element(By.ID, "start").click()
        print("Listening...")
        msg="[green]Listening........[/green]"

        wait = WebDriverWait(driver, timeout)
        text = ""

        try:
            text = wait.until(lambda d: d.find_element(By.ID, "output").text.strip().lower() or False)
        except TimeoutException:
            return {"error": True, "message": "No speech detected within timeout"}

        driver.find_element(By.ID, "end").click()

        words = text.split()
        if any(q in words for q in question_words):
            if not text.endswith(("?", ".", "!")):
                text += "?"

        return {"error": False, "translated": text}

    except Exception as e:
        return {"error": True, "message": str(e)}

def translate_to_english(text):
    if not text:
        msg="[red]No text recognized[/red]"
        return msg
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        msg="[red]I can not Understand what you Say.[/red]"
        return text
