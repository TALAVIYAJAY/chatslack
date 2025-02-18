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
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HUGGINGFACE_MODEL_URL = os.getenv("HUGGINGFACE_MODEL_URL")

# Cache to store processed event IDs
event_cache = set()

# Function to generate LLM ANSWER
def get_llama3_response(query, chat_history):
    """Calls the Hugging Face API to get a response for the query, including chat history."""

    print("User Message:", query)
    print('\n----------------------\n')
    print("User Last 5 chat history:", chat_history)
    print('\n----------------------\n')

    parameters = {
        "max_new_tokens": 1000,  # Increase max tokens
        "temperature": 0.7,  # Relax the temperature for more varied responses
        "top_k": 50,  # Can try increasing or decreasing this for varied results
        "top_p": 0.9,  # Relax the top_p for broader responses
        "return_full_text": False
    }

    # Format chat history for prompt
    history_text = ""
    for item in chat_history:
        history_text += f"<|start_header_id|>user<|end_header_id|> {item['user']}<|eot_id|>\n"
        history_text += f"<|start_header_id|>assistant<|end_header_id|> {item['bot']}<|eot_id|>\n"

    # Construct the final prompt with chat history
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful and smart assistant. You accurately provide answers to the provided user query.<|eot_id|>
{history_text}
<|start_header_id|>user<|end_header_id|> Here is the query: ```{query}```.
Provide a precise and concise answer in less than 50 words. Ensure sentences are complete and not cut off mid-word.<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    headers = {
        'Authorization': f'Bearer {HUGGINGFACE_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {"inputs": prompt, "parameters": parameters}

    try:
        response = requests.post(HUGGINGFACE_MODEL_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Ensure response is valid JSON
        response_data = response.json()
        print("Full API Response:", response_data)  # Log the full response for better debugging
        
        # Extract response text safely
        generated_text = response_data[0].get('generated_text', "").strip() if response_data else ""
        if not generated_text:
            print("Error: No generated text in response.")
            return "I'm sorry, but I couldn't generate a response at the moment. Please try again."

        # Ensure response is within 50 words and does not cut sentences
        words = generated_text.split()
        if len(words) > 50:
            truncated_response = " ".join(words[:50])
            if "." in truncated_response:
                truncated_response = truncated_response.rsplit(".", 1)[0] + "."  # Ensure a full sentence
            return truncated_response

        return generated_text

    except requests.exceptions.RequestException as req_err:
        print(f"Request Error: {req_err}")
    except KeyError as key_err:
        print(f"Key Error: {key_err}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

    # Return a fallback response if an error occurs
    return "I'm sorry, but I'm unable to process your request at the moment. Please try again later."

# Function to Send LLM ANSWER to Slack
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

# Function to handle user query from slack
@csrf_exempt
def slack_event_listener(request):
    """Handles Slack events and ensures only valid messages are processed."""
    try:
        # Log raw request body for debugging
        raw_body = request.body.decode("utf-8")
        print("Raw Request Body:", raw_body)

        # Handle empty request body
        if not raw_body:
            return JsonResponse({"error": "Empty request body"}, status=400)

        # Parse JSON safely
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON received"}, status=400)

        # Handle Slack URL verification challenge
        if "challenge" in data:
            return JsonResponse({"challenge": data["challenge"]})

        event = data.get("event", {})
        event_id = data.get("event_id")  # Get event ID to prevent duplicate processing
        user_message = event.get("text", "").strip()
        channel = event.get("channel")
        event_type = event.get("type")
        bot_id = event.get("bot_id")  # Ignore bot messages
        user_id = event.get("user")  # Extract user ID

        # Ignore bot messages & non-message events
        if bot_id or event_type != "message" or not user_message:
            return JsonResponse({"status": "ignored"})

        # Ignore system messages (join/leave events)
        if "has joined the channel" in user_message.lower() or "has left the channel" in user_message.lower():
            print(f"Ignored system message: {user_message}")
            return JsonResponse({"status": "ignored"})

        # Prevent duplicate event processing
        if event_id in event_cache:
            print(f"Duplicate event detected: {event_id}")
            return JsonResponse({"status": "ignored"})
        event_cache.add(event_id)

        print('\n----------------------\n')
        print("Received Slack Message from User ID:", user_id)

        # Fetch last 5 conversations from PostgreSQL
        last_5_conversations = cs.objects.filter(user_id=user_id,channel_id=channel).order_by('-created_at')[:5]

        # Reverse order so the oldest appears first
        last_5_conversations = list(last_5_conversations)[::-1]

        # Format history for Llama3 API
        history = [{"user": conv.user_input, "bot": conv.bot_response} for conv in last_5_conversations]

        # Send user input to Hugging Face API
        bot_response = get_llama3_response(user_message,history)
        print("Generated Bot Response:", bot_response)

        # Save conversation to PostgreSQL
        cs.objects.create(user_id=user_id, channel_id=channel, user_input=user_message, bot_response=bot_response)

        # Send response to Slack
        send_slack_message(channel, bot_response)

        return JsonResponse({"status": "ok"})

    except Exception as e:
        print(f"Slack Event Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# Function to render home page(Default Page)
def home(request):
    """Renders the home page with Slack instructions."""
    return render(request, 'home.html')


