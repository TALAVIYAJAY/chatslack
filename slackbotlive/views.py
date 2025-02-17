import os
import json
import requests
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from django.shortcuts import render
from .models import cs

# Load environment variables
load_dotenv()

# Slack and Hugging Face credentials
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HUGGINGFACE_MODEL_URL = os.getenv("HUGGINGFACE_MODEL_URL")


def get_gpt3_response(user_input, history):
    """Calls the Hugging Face API to get a response from GPT-3."""
    parameters = {
        "max_new_tokens": 500,
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.95,
        "return_full_text": False
    }

    # Format chat history for GPT-3
    formatted_history = "\n".join([f"User: {conv['user']}\nAssistant: {conv['bot']}" for conv in history])
    prompt = f"{formatted_history}\nUser: {user_input}\nAssistant:"

    headers = {
        'Authorization': f'Bearer {HUGGINGFACE_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {"inputs": prompt, "parameters": parameters}

    try:
        response = requests.post(HUGGINGFACE_MODEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data[0]['generated_text'].strip() if 'generated_text' in response_data[0] else "Error in API response."
    except Exception as e:
        print("Error:", e)
        return "I am unable to provide an answer at the moment. Please try again later."


def send_slack_message(channel, text):
    """Sends a message to Slack."""
    print("Sending message to Slack:", text)
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel,
        "text": text
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        print("Slack Response:", response_data)
        return response_data
    except requests.exceptions.RequestException as e:
        print("Error sending message to Slack:", e)
        return {"error": "Failed to send message to Slack"}


@csrf_exempt
def slack_event_listener(request):
    """Handles Slack events and ensures only valid messages are processed."""
    try:
        raw_body = request.body.decode("utf-8")
        print("Raw Request Body:", raw_body)

        if not raw_body:
            return JsonResponse({"error": "Empty request body"}, status=400)

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON received"}, status=400)

        if "challenge" in data:
            return JsonResponse({"challenge": data["challenge"]})

        event = data.get("event", {})
        user_message = event.get("text", "").strip()
        channel = event.get("channel")
        event_type = event.get("type")
        bot_id = event.get("bot_id")
        user_id = event.get("user")

        if bot_id or event_type != "message" or not user_message:
            return JsonResponse({"status": "ignored"})

        if "has joined the channel" in user_message.lower() or "has left the channel" in user_message.lower():
            print(f"Ignored system message: {user_message}")
            return JsonResponse({"status": "ignored"})

        print("Received Slack Message from User ID:", user_id)
        print("User Message:", user_message)

        # Fetch last 5 conversations from PostgreSQL
        last_5_conversations = cs.objects.filter(user_id=user_id).order_by('-created_at')[:5]

        # Reverse order so the oldest appears first
        last_5_conversations = list(last_5_conversations)[::-1]

        # Format history for GPT-3 API
        history = [{"user": conv.user_input, "bot": conv.bot_response} for conv in last_5_conversations]

        print("User Input Message:", user_message)
        print("User Last 5 Chat History:", history)

        # Send user input + history to Hugging Face
        bot_response = get_gpt3_response(user_message, history)
        print("Generated Bot Response:", bot_response)

        # Save conversation to PostgreSQL
        cs.objects.create(user_id=user_id, user_input=user_message, bot_response=bot_response)

        # Send response to Slack
        send_slack_message(channel, bot_response)

        return JsonResponse({"status": "ok"})

    except Exception as e:
        print(f"Slack Event Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def home(request):
    """Renders the home page with Slack instructions."""
    return render(request, 'home.html')


def slack_oauth_callback(request):
    """Handles OAuth callback after Slack authentication."""
    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Authorization code not found"}, status=400)

    token_url = "https://slack.com/api/oauth.v2.access"
    payload = {
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code
    }

    try:
        response = requests.post(token_url, data=payload)
        response_data = response.json()

        if not response_data.get("ok"):
            return JsonResponse({"error": response_data.get("error", "OAuth failed")}, status=400)

        access_token = response_data.get("access_token")
        team_name = response_data.get("team", {}).get("name")

        print(f"Slack OAuth Success: {team_name} - Token: {access_token}")

        return HttpResponseRedirect("/")  # Redirect to home after successful login

    except requests.exceptions.RequestException as e:
        print(f"OAuth Request Error: {e}")
        return JsonResponse({"error": "OAuth request failed"}, status=500)
