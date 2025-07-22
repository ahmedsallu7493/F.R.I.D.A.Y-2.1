import requests
from datetime import datetime
from groq import Groq
from dotenv import dotenv_values

# Load Groq API key from .env
env = dotenv_values(".env")
GroqAPIKey = env.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

def format_to_ampm(dt_string):
    try:
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S%z")
        return dt.strftime("%I:%M %p")
    except ValueError:
        return "N/A"

def get_weather_report(city="Surat", state="Gujarat", lat="21.1702", lon="72.8311"):
    url = f"https://weather-api180.p.rapidapi.com/weather/weather/{lat}/{lon}/current"
    headers = {
        "x-rapidapi-key": "ae5a5fdf88msha285a7f3ee6a345p1e4365jsna90053488b92",
        "x-rapidapi-host": "weather-api180.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", {})

        # Prepare weather facts
        weather_facts = {
            "city": city,
            "state": state,
            "updated_time": format_to_ampm(data.get("validTimeLocal", "")),
            "temperature": data.get("temperature", "N/A"),
            "feels_like": data.get("temperatureFeelsLike", "N/A"),
            "condition": data.get("wxPhraseLong", "N/A"),
            "humidity": data.get("relativeHumidity", "N/A"),
            "wind_speed": data.get("windSpeed", "N/A"),
            "wind_dir": data.get("windDirectionCardinal", "N/A"),
            "visibility": data.get("visibility", "N/A"),
            "uv_index": data.get("uvIndex", "N/A"),
            "uv_desc": data.get("uvDescription", "N/A"),
            "sunrise": format_to_ampm(data.get("sunriseTimeLocal", "")),
            "sunset": format_to_ampm(data.get("sunsetTimeLocal", ""))
        }

        # Format input prompt for Groq
        prompt = (
            f"Create a natural-sounding weather report for {city}, {state}:\n"
            f"- Updated: {weather_facts['updated_time']}\n"
            f"- Temp: {weather_facts['temperature']}°C, feels like {weather_facts['feels_like']}°C\n"
            f"- Condition: {weather_facts['condition']}\n"
            f"- Humidity: {weather_facts['humidity']}%\n"
            f"- Wind: {weather_facts['wind_speed']} km/h from {weather_facts['wind_dir']}\n"
            f"- Visibility: {weather_facts['visibility']} km\n"
            f"- UV Index: {weather_facts['uv_index']} ({weather_facts['uv_desc']})\n"
            f"- Sunrise: {weather_facts['sunrise']}, Sunset: {weather_facts['sunset']}\n\n"
            f"Now convert this into a friendly report like a virtual assistant would say."
        )

        # Send to Groq LLaMA model
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that speaks like a human."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300,
            top_p=1,
            stream=True
        )

        # Collect streamed content
        response_text = ""
        for chunk in completion:
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                response_text += content

        return response_text.strip()

    except requests.exceptions.RequestException as e:
        return f"⚠️ Network Error: {str(e)}"
    except Exception as e:
        return f"⚠️ Unexpected Error: {str(e)}"


# For testing
if __name__ == "__main__":
    print(get_weather_report())
