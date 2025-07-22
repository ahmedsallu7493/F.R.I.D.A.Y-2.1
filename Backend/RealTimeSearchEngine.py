from googlesearch import search
from groq import Groq
from json import load, dump
from dotenv import dotenv_values
import datetime
import os
from rich import print


# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistance = env_vars.get("Assistance", "AI Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    raise ValueError("Error: GroqAPIKey is missing in .env file")

client = Groq(api_key=GroqAPIKey)
chat_log_path = os.path.join("Data", "ChatLog.json")


# Load/Save Chat Logs
def load_chat_log():
    if not os.path.exists(chat_log_path):
        with open(chat_log_path, "w") as f:
            dump([], f)
    with open(chat_log_path, "r") as f:
        return load(f)


def save_chat_log(messages):
    with open(chat_log_path, "w") as f:
        dump(messages, f, indent=4)


# Modify the answer to remove unwanted text
def answer_modifier(answer):
    blacklist_phrases = [
        "I'm a large language model",
        "Please note that",
        "I suggest checking",
        "You can also search for",
        "reliable weather website",
        "Weather.com",
        "AccuWeather",
        "News channel",
        "mobile app",
        "look for local news",
        "<|header_start|>",
        "<|header_end|>",
        "Is there anything else I can help you with?",
        "Let me know if",
        "I can't access real-time",
    ]

    stop_keywords = [
        "Sunset",  # Weather
        "Volume",  # Stock market
        "Today's top news headlines are:"  # News start
    ]

    cleaned_lines = []
    seen_lines = set()
    stop_triggered = False

    for line in answer.splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # Skip blacklisted lines
        if any(bad.lower() in stripped_line.lower() for bad in blacklist_phrases):
            continue

        # Stop after key lines
        if any(stripped_line.startswith(key) for key in stop_keywords):
            stop_triggered = True
            continue

        if stop_triggered:
            continue

        if stripped_line not in seen_lines:
            cleaned_lines.append(stripped_line)
            seen_lines.add(stripped_line)

    return "\n".join(cleaned_lines)



def real_time_info():
    now = datetime.datetime.now()
    return (
        f"Use this real-time information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%m')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Hour: {now.strftime('%H')}\n"
        f"Minute: {now.strftime('%M')}\n"
        f"Second: {now.strftime('%S')}\n"
    )


def google_search(query):
    try:
        results = list(search(query, num=5))
        return f"The search results for '{query}' are:\n[start]\n" + "\n".join(
            [f"{i + 1}. {link}" for i, link in enumerate(results)]
        ) + "\n[end]"
    except Exception as e:
        return f"[red]Error occurred during Google search: {str(e)}[/red]"


def detect_intent(prompt):
    keywords = {
        "weather": ["weather", "temperature", "climate"],
        "stock": ["stock", "share", "market", "price"],
        "news": ["news", "headlines", "update"]
    }
    for intent, words in keywords.items():
        if any(word in prompt.lower() for word in words):
            return intent
    return "general"


def extract_stock_symbol(prompt):
    instruction = (
        "Extract only the stock symbol or company name from this query. "
        "For example, from 'What is the stock price of Tata?' return 'TCS' or 'TATA'. No explanation."
    )

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=20,
        stream=False
    )

    content = response.choices[0].message.content
    return content.strip().upper()


def call_module(prompt):
    intent = detect_intent(prompt)

    if intent == "weather":
        from weather_module import get_weather_report
        
        return answer_modifier(get_weather_report(prompt))

    elif intent == "stock":
        from stock_module import get_stock_info
        company = extract_stock_symbol(prompt)
        mapping = {
            "TATA": "TCS.NS",
            "TCS": "TCS.NS",
            "RELIANCE": "RELIANCE.NS",
            "INFOSYS": "INFY.NS",
            "HDFC": "HDFCBANK.NS"
        }
        symbol = mapping.get(company, company + ".NS")
        return answer_modifier(get_stock_info(symbol))

    elif intent == "news":
        from news_module import get_important_news
        return answer_modifier(get_important_news())

    return None


system_instructions = f"""You are {Assistance}, a helpful AI assistant.
Answer queries in clear and friendly natural language.
Do not return raw code, JSON, or API responses unless the user explicitly asks for code.
Never begin answers with "import", "def", or "print" unless asked to write code.
Avoid technical formats unless absolutely required.
Only answer in natural English as if you're having a conversation.
"""



def RealtimeSearchEngine(prompt):
    try:
        intent = detect_intent(prompt)

        # Handle weather, stock, and news internally using local modules
        if intent in ["weather", "stock", "news"]:
            return call_module(prompt)

        # For all other prompts, use external LLaMA model
        messages = load_chat_log()
        messages.append({"role": "user", "content": prompt})

        search_result = google_search(prompt)

        system_chat = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": f"Here are the search results to help you answer: {search_result}"},
            {"role": "user", "content": f"Use this real-time info: {real_time_info()}"},
            {"role": "user", "content": prompt}
        ]


        full_context = system_chat + messages

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=full_context,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True
        )

        answer = ""
        for chunk in completion:
            content = getattr(chunk.choices[0].delta, 'content', None)
            if content:
                answer += content

        answer = answer.strip().replace("</s>", " ")
        return answer_modifier(answer)

    except Exception as e:
        return f"[red]An error occurred: {str(e)}[/red]"


if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ").strip()
        if not prompt:
            continue
        print(RealtimeSearchEngine(prompt))
