import os
import sys
import time
import re
import pyautogui
from AppOpener import open as appopen
from AppOpener import close
from dotenv import dotenv_values
from groq import Groq

# Enable emergency mouse fail-safe
pyautogui.FAILSAFE = True

# === Load API key ===
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
client = Groq(api_key=GroqAPIKey)

# === Extract contact and message from free-form query ===
def extract_contact_and_message(user_query):
    extract_prompt = """
You are an assistant that extracts:
1. Contact name
2. Message to send

Rules:
- Input is a casual sentence like "Send message to SK: kem che bhai"
- Output format must be:
Name=<ContactName>
Message=<MessageToSend>

Don't add any explanation or comments.
"""

    try:
        response = client.chat.completions.create(
            model="compound-beta",  # or llama-3-8b-8192 if available
            messages=[
                {"role": "system", "content": extract_prompt.strip()},
                {"role": "user", "content": user_query.strip()}
            ],
            max_tokens=100,
            temperature=0.3,
            top_p=1,
            stream=False
        )

        output = response.choices[0].message.content.strip()

        match = re.search(r'Name=(.*)\nMessage=(.*)', output, re.IGNORECASE)
        if match:
            contact = match.group(1).strip()
            message = match.group(2).strip()
            return contact, message
        else:
            print("❌ Couldn't extract properly. Using fallback.")
            return "Unknown", user_query

    except Exception as e:
        print(f"❌ AI extract error: {e}")
        return "Unknown", user_query

# === Rewrite message politely ===
def professionalize_message(contact_name, raw_msg):
    system_prompt = """
You are a polite message rewriter bot.

Your task:
- Receive input in Hinglish, Gujlish, or English: "ContactName: message"
- Return only the rewritten message.
- It must be in the same language.
- No explanation, no thoughts, no description.

Examples:
"A.Sallu: tu kab ayega?" → "Tu kab aayega, please confirm."
"SK: kale kaam che" → "Kale kaam chhe. Please update soon."
"""

    user_input = f"{contact_name}: {raw_msg}"

    try:
        response = client.chat.completions.create(
            model="compound-beta",
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_input.strip()}
            ],
            max_tokens=300,
            temperature=0.7,
            top_p=1,
            stream=False
        )

        full_reply = response.choices[0].message.content.strip()

        # Extract clean line from response
        lines = full_reply.splitlines()
        candidates = [line for line in lines if 5 < len(line.strip()) < 200 and not line.lower().startswith(("i think", "now", "let", "looking", "alright", "as an ai"))]

        clean_reply = candidates[-1] if candidates else raw_msg

        return contact_name, clean_reply

    except Exception as e:
        print(f"❌ AI error: {e}")
        return contact_name, raw_msg

# === Send message to WhatsApp ===
def optimized_send_whatsapp_message(contact_name, message):
    try:
        print("📲 Opening WhatsApp...")
        appopen("whatsapp", match_closest=True, throw_error=True)
        time.sleep(8)

        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(2)

        pyautogui.write(contact_name.strip(), interval=0.05)
        time.sleep(1.5)
        pyautogui.press('tab')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1.5)

        # Replace with actual coordinates if needed
        pyautogui.click(x=680, y=740)
        time.sleep(0.5)

        pyautogui.write(message, interval=0.05)
        pyautogui.press('enter')

        print(f"✅ Message sent to {contact_name}")
        print("📴 Closing WhatsApp...")
        time.sleep(2)
        close("whatsapp", match_closest=True, throw_error=True)

    except Exception as e:
        print(f"❌ WhatsApp Error: {e}")
        sys.exit(1)

# === Main flow ===
def msg_from_query():
    user_query = input("🎙️ Say something like: 'Send message to Bhavesh: bhai tuition ma avse?'\n>> ")

    # Step 1: Extract contact & message
    contact, raw_msg = extract_contact_and_message(user_query)
    print(f"📛 Contact: {contact}")
    print(f"✍️ Original Msg: {raw_msg}")

    # Step 2: Rewrite message
    _, refined_msg = professionalize_message(contact, raw_msg)
    print(f"💬 Final Msg: {refined_msg}")

    # Step 3: Send to WhatsApp
    optimized_send_whatsapp_message(contact, refined_msg)

    print(f"⏱️ Total time: {time.time() - start:.2f} seconds")

# === Entry point ===
if __name__ == "__main__":
    start = time.time()
    msg_from_query()
