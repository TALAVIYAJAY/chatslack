import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from .models import cs

# Load environment variables
load_dotenv()

# Slack and Hugging Face credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HUGGINGFACE_MODEL_URL = os.getenv("HUGGINGFACE_MODEL_URL")

def get_llama3_response(user_input, history):

    #OPTION 1 : HUGGING FACE
    # """Sends user input and past context to Hugging Face API once. If it fails, returns 'NA'."""
    # headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    # payload = {
    #     "inputs": user_input,
    #     "parameters": {"max_new_tokens": 200, "temperature": 0.7},
    #     "history": history  # ✅ Pass previous context to API
    # }

    # try:
    #     response = requests.post(HUGGINGFACE_MODEL_URL, headers=headers, json=payload, timeout=60)
    #     response_data = response.json()

    #     # ✅ Handle Hugging Face errors
    #     if isinstance(response_data, dict) and "error" in response_data:
    #         return "NA"

    #     # ✅ Extract response text from list
    #     if isinstance(response_data, list) and len(response_data) > 0 and "generated_text" in response_data[0]:
    #         return response_data[0]["generated_text"]

    # except requests.exceptions.RequestException as e:
    #     print(f"Request error: {e}")

    #OPTION 2 : DEFAULT ANSWER
    return "DEFAULT ANSWER IS SETUP"


def send_slack_message(channel, text):
    """Sends a message to Slack."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel,
        "text": text
    }
    response = requests.post(url, headers=headers, json=payload)
    
    print("Slack Response:", response.json())  # ✅ Debugging
    return response.json()

@csrf_exempt
def slack_event_listener(request):
    """Handles Slack events and ensures only valid messages are processed."""
    try:
        data = json.loads(request.body)

        # ✅ Handle Slack challenge verification
        if "challenge" in data:
            return JsonResponse({"challenge": data["challenge"]})

        event = data.get("event", {})
        user_message = event.get("text", "").strip()
        channel = event.get("channel")
        event_type = event.get("type")
        bot_id = event.get("bot_id")  # BOT ID (IGNORE BOT MESSAGES)
        user_id = event.get("user")  # ✅ EXTRACT USER ID

        # ✅ Ignore bot messages & non-message events
        if bot_id or event_type != "message" or not user_message:
            return JsonResponse({"status": "ignored"})

        # ✅ Ignore system messages (join/leave events)
        if "has joined the channel" in user_message.lower() or "has left the channel" in user_message.lower():
            print(f"Ignored system message: {user_message}")  # ✅ Debugging
            return JsonResponse({"status": "ignored"})

        print("\n---------------------\n")
        print(f"Received Slack Message from User ID : {user_id}")  # ✅ Debugging
        print("\n---------------------\n")

        # ✅ Fetch last 5 conversations (descending order)
        last_5_conversations = cs.objects.filter(user_id=user_id).order_by('-created_at')[:5]

        # ✅ Format history for Llama3 API
        history = [{"user": conv.user_input, "bot": conv.bot_response} for conv in last_5_conversations]

        print(f"User Input Message: {user_message}")  # ✅ Debugging
        print("\n---------------------\n")
        print(f"User Last 5 chat history: {history}")  # ✅ Debugging
        print("\n---------------------\n")

        # ✅ Send user input + history to Hugging Face
        bot_response = get_llama3_response(user_message, history)

        # ✅ Save conversation to PostgreSQL
        cs.objects.create(user_id=user_id, user_input=user_message, bot_response=bot_response)

        # ✅ Send response to Slack
        send_slack_message(channel, bot_response)

        return JsonResponse({"status": "ok"})

    except Exception as e:
        print(f"Slack Event Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def home(request):
    """Basic home route to check if Django server is running."""
    return JsonResponse({"message": "Slack Bot is Running!"})
