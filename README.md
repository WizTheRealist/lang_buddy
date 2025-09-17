# LangBuddy

An interactive web app that helps users practice English conversations with an AI tutor powered by Google Gemini.
It supports real-time chat, topic selection, and tracks user learning progress.

## Features

- 🗨️ **Real-time Chat:** Converse with an AI tutor using WebSockets.

- 🎯 **Topic-based Practice:** Choose topics like Travel, Business, Academic, or Conversational.

- 🔑 **Authentication:** Sign up, log in, and manage your learning sessions.

- 📊 **Dashboard:** View your total messages, favorite topic, streaks, and weekly activity.

- 📅 **Daily Tracking:** Counts your daily messages and topics practiced.

- 🤖 **AI Responses:** Uses Google Gemini to generate clear, short replies.

## Tech Stack

- **Backend:** Django, Django Channels (WebSockets)

- **Frontend:** Django Templates (HTML, CSS, JS)

- **Database:** SQLite / PostgreSQL

- **AI:** Google Gemini (via google-genai client)

- **Auth:** Django built-in authentication system

## How It Works

1. Users sign up or log in to access the chat.

2. A topic (e.g., Travel, Business) can be selected to guide the conversation.

3. Messages are sent via WebSockets to the AI tutor.

4. The app stores the conversation in the database and updates:

    - User progress (total messages, favorite topic, streaks).

    - Daily activity (messages sent and topics practiced).

5. The dashboard shows statistics, recent activity, and practice history.

## Setup & Run

1. Clone the repo

    `git clone <repo-url>`
    
    `cd ai-english-tutor`

2. Create and activate virtual environment

    `python -m venv venv`
    
    `source venv/bin/activate`   # On Linux/Mac
    
    `venv\Scripts\activate`      # On Windows

3. Install dependencies

    `pip install -r requirements.txt`

4. Add your Gemini key to .env

    `GEMINI_API_KEY`=your_api_key_here

5. Run migrations

    `python manage.py migrate`

6. Start the server with Daphne

    `daphne lang_buddy.asgi:application`

7. Open in browser

    `http://127.0.0.1:8000`

## Example Use Case

- A learner selects Travel as the topic.

- They start chatting with the AI: “How do I ask for directions?”

- The AI replies in simple English, continuing the conversation naturally.

- The learner’s messages are tracked and shown on their dashboard for progress.

