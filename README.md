
# **Jay_Talaviya's Droid - Slack Chatbot** 🤖  

## **Overview**  
Jay_Talaviya's Droid is an AI-powered Slack chatbot that listens to tagged questions in a channel, sends the queries (along with the last 5 messages) to an LLM, and responds with AI-generated answers. The bot is built using Django, PostgreSQL, and the **Hugging Face LLaMA 3 model** for response generation.

## **Features**  
✅ **Seamless Slack Integration** – Add the bot to your Slack workspace and start chatting!  
✅ **Memory-Aware Conversations** – Sends the last 5 messages (including both user and bot responses) to the LLM for context-aware replies.  
✅ **Hugging Face LLaMA 3 Powered** – Ensures high-quality AI-generated answers.  
✅ **Deployed on Render** – Fully hosted backend with a user-friendly Slack authentication page.  
✅ **Secure & Scalable** – Built with Django and PostgreSQL for efficient message storage and retrieval.  

## **Architecture Design**

This system consists of the following key components:

### **User Interaction (Slack)**  
- Users send messages to the Slack chatbot in a channel.

### **Django Backend (Deployed on Render)**  
- The Django app receives and processes the Slack messages.  
- It fetches the last 5 user-bot interactions from the PostgreSQL database for context.

### **PostgreSQL Database (Deployed on Render)**  
- Stores chat history, including user inputs and bot responses.

### **Hugging Face API (LLaMA 3 Model)**  
- The user query and conversation history are sent to the Hugging Face LLaMA 3 model to generate a response.

### **Slack API (Response Delivery)**  
- The bot's response is sent back to the Slack channel.


#### **Flow**  
1. User sends a message on Slack.  
2. Django backend processes the message and retrieves the last 5 conversations from PostgreSQL.  
3. The query and history are sent to Hugging Face for response generation.  
4. The response is sent back to Slack and saved in the database.


#### **Tech Stack**  
- **Backend**: Django (Python)  
- **Database**: PostgreSQL  
- **LLM**: Hugging Face LLaMA 3  
- **Hosting**: Render  
- **Messaging**: Slack API

## **Setup & Installation**  

### **Run the Project Locally**  
#### **Prerequisites**  
- Python 3.x  
- PostgreSQL  

#### **Clone the Repository**  
```sh
git clone https://github.com/TALAVIYAJAY/chatslack.git
cd chatslack
```

#### **Set Up Virtual Environment**  
```sh
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows
```

#### **Install Dependencies**  
```sh
pip install -r requirements.txt
```

#### **Set Up Environment Variables**  
Create a `.env` file in the root directory and add the following:  
```env
SLACK_BOT_TOKEN=your_slack_bot_token
HUGGINGFACE_TOKEN=your_huggingface_token
HUGGINGFACE_API_KEY=your_huggingface_api_key
DATABASE_URL=your_postgresql_database_url
```

#### **Run Migrations**  
```sh
python manage.py migrate
```

#### **Start the Django Server**  
```sh
python manage.py runserver
```

## **Jay Talaviya's Droid Deployment on Render**  
The app is already deployed! You can check it out here:  
📌 **[Live Demo on Render](https://chat-slack-live.onrender.com/)**  

## **Add Jay_Talaviya's Droid to a Slack channel**  
To add the bot to your Slack channel, type the following command: 
```sh
/invite @Jay_Talaviya's Droid
```
Setup Example Question to Ask the Droid: 
```sh
@Jay_Talaviya's Droid explain Law of Thermodynamics
```

## **Demo Video 🎥**  
📌 **[Watch the chatbot in action](INSERT_VIDEO_DEMO_LINK_HERE)**  

## **Architecture Diagram 🏗️**  
📌 **[View the system architecture](INSERT_ARCHITECTURE_DIAGRAM_LINK_HERE)**  

## **Contributing**  
Want to improve the chatbot? Feel free to fork the repository and submit a PR!  

## **Contact**  
📧 **Email**: talaviyajay10@gmail.com 
🔗 **LinkedIn**: https://www.linkedin.com/in/jay-talaviya-ab5b0b1b6/ 



