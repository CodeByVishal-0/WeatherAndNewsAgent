from dotenv import load_dotenv
load_dotenv()

import os
import requests

from tavily import TavilyClient
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    SystemMessage
)

# =========================
# WEATHER TOOL
# =========================

@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""

    try:
        api_key = os.getenv("OPEN_WEATHER_API_KEY")

        if not api_key:
            return "OpenWeather API key missing."

        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={api_key}&units=metric"
        )

        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return f"Weather Error: {data.get('message')}"

        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"]

        return (
            f"Weather in {city}:\n"
            f"- Condition: {desc}\n"
            f"- Temperature: {temp}°C\n"
            f"- Feels Like: {feels}°C\n"
            f"- Humidity: {humidity}%"
        )

    except Exception as e:
        return f"Weather Tool Error: {str(e)}"


# =========================
# NEWS TOOL
# =========================

tavily_client = TavilyClient()


@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""

    try:
        response = tavily_client.search(
            query=f"Latest news about {city}",
            search_depth="basic",
            max_results=3
        )

        results = response.get("results", [])

        if not results:
            return f"No news found for {city}"

        news_list = []

        for idx, news in enumerate(results, start=1):

            title = news.get("title", "No title")
            content = news.get("content", "No content")
            url = news.get("url", "")

            news_list.append(
                f"{idx}. {title}\n"
                f"{content}\n"
                f"Source: {url}\n"
            )

        return f"Latest News about {city}:\n\n" + "\n".join(news_list)

    except Exception as e:
        return f"News Tool Error: {str(e)}"


# =========================
# LLM SETUP
# =========================

llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

tools = {
    "get_weather": get_weather,
    "get_news": get_news
}

llm_with_tools = llm.bind_tools(
    [get_weather, get_news]
)


# =========================
# SYSTEM PROMPT
# =========================

system_prompt = SystemMessage(
    content=(
        "You are a City Intelligence Assistant.\n"
        "You help users with:\n"
        "- Weather information\n"
        "- Latest city news\n"
        "Use tools whenever required."
    )
)


# =========================
# AGENT LOOP
# =========================

messages = [system_prompt]

print("\n===== City Intelligence System =====")
print("Type '0' to exit.\n")

while True:

    user_input = input("You: ")

    if user_input == "0":
        print("Goodbye!")
        break

    messages.append(HumanMessage(content=user_input))

    while True:

        result = llm_with_tools.invoke(messages)
        print(result.content)


        messages.append(result)

        # =========================
        # TOOL CALLING
        # =========================

        if result.tool_calls:

            for tool_call in result.tool_calls:

                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                print(f"\nAgent wants to use tool: {tool_name}")
                print(f"Arguments: {tool_args}")

                confirm = input("Approve? (y/n): ")

                if confirm.lower() != "y":
                    print("Tool call denied.\n")
                    continue

                # Execute tool
                tool_result = tools[tool_name].invoke(tool_args)

                print(f"\nTool Output:\n{tool_result}\n")

                messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"]
                    )
                )

            continue
        # =========================
        # FINAL RESPONSE
        # =========================

        else:
            print(f"\nAssistant: {result.content}\n")
            break