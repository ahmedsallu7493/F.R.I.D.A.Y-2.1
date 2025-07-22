# Model.py
import cohere
from rich import print
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
cohere_api_key = env_vars.get("COHERE_API_KEY")

# Initialize Cohere client
co = cohere.Client(api_key=cohere_api_key)

# List of supported functions
funcs = ["exit", "general", "realtime", "open", "close", "play", "generate-image", "system", "content", "google search", "youtube search", "reminder","follow","unfollow"]

# List to store messages
messages = []

# Preamble for the Cohere model
preamble = '''
You are a very Accurate Decision Making Model which decides what kind of query is given to you. You will decide whether a query is a "general" query, a "realtime" query, or a query which is asking you to perform any task or automation like opening WhatsApp or Instagram.
"""You don't answer any query, you just decide what kind of query is given to you."""
-> Respond with "general query" if a query can be answered by an LLM model (Conversational AI Chatbot) and does not require any up-to-date information.
-> Respond with "realtime query" if a query cannot be answered by an LLM model (because it doesn't have real-time data) and requires up-to-date data.
-> Respond with "open (application name or website name)" if a query is asking you to open any application like WhatsApp or Instagram, etc.
-> Respond with "close (application name or website name)" if a query is asking you to close any application like Notepad or Instagram, etc.
-> Respond with "play (song name)" if a query is asking you to play a song like "Way of Tears" or "Al Quds", etc.
-> Respond with "generate image (image prompt)" if a query is requesting to generate an image of any prompt like "generate image of a lion" or "generate image of a car", etc.
-> Respond with "reminder (date or time)" if a query is requesting you to remind at a particular time.
-> Respond with "system (task)" if a query is asking you to mute, unmute, volume up, or volume down, etc.
-> Respond with "content (topic)" if a query is asking you to write content on a specific topic, emails, code, etc.
-> Respond with "google (topic)" if a query is asking you to Google search on a specific topic.
-> Respond with "youtube (topic)" if a query is asking you to search for any specific topic on YouTube.
-> Respond with "message"if a query is asking you to send Message to anyone.
If a user is saying goodbye and wants to end the conversation like "bye FRIDAY", respond with "exit".
Respond with "general query" if you can't decide the kind of query or if a query asks you to perform a task which does not exist.
If the user says multiple queries at a time, analyze it and divide it according to the above sentences.
'''

# Chat history for context
chat_history = [
    {"role": "user", "message": "How are you?"},
    {"role": "chatbot", "message": "general How are you?"},
    {"role": "user", "message": "Do you like Pizza?"},
    {"role": "chatbot", "message": "general Do you like Pizza?"},
    {"role": "user", "message": "Open Chrome and tell me about Mahatma Gandhi"},
    {"role": "chatbot", "message": "open Chrome, general Tell me about Mahatma Gandhi."},
    {"role": "user", "message": "Open Chrome and Firefox"},
    {"role": "chatbot", "message": "open Chrome, open Firefox"},
    {"role": "user", "message": "What's today's date and by the way remind me Happy Birthday on 24 March at 12am"},
    {"role": "chatbot", "message": "general What's today's date, reminder 12am 24 March Happy Birthday"},
    {"role": "user", "message": "Chat with me."},
    {"role": "chatbot", "message": "general Chat with me."}
]

def firstlayer(prompt: str = "test"):
    # Add user message to the messages list
    messages.append({"role": "user", "content": f"{prompt}"})

    # Stream response from Cohere
    stream = co.chat(
    model='command-r-plus',
    message=prompt,
    temperature=0.7,
    chat_history=chat_history,
    preamble=preamble,
    connectors=[],
    prompt_truncation='off'
    ).text  # Extracts the response text

    # Add chatbot response to the messages list
    messages.append({"role": "chatbot", "content": stream})

    return stream


# Interactive loop for user input
def interactive_loop():

    while True:
        # Take input from the user
        user_input = input("You: ")
               
        # Process the user input
        response = firstlayer(user_input)
        print(f"{response}")

# Run the interactive loop
if __name__ == "__main__":
    interactive_loop()