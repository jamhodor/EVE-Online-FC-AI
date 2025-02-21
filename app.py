import google.generativeai as genai
import sqlite3
import os
from langchain.prompts import PromptTemplate
from flask import Flask, request, render_template, g, redirect, url_for
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Your Google Cloud API key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Get from environment variable
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.  Please set it.")

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# Select the Gemini model
model = genai.GenerativeModel("gemini-1.5-pro-latest")  # or gemini-pro, etc.

# Database setup
DB_FILE = "chatbot_conversation.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILE)
        # Create the conversations table, adding a name field
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                user_input TEXT,
                chatbot_response TEXT
            )
        """)
        db.commit()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Define the prompt template using LangChain
template = """You are an AI assistant to the fleet commanders in the online game Eve Online. You will give short advice on how to act or react in scenarios given by the user. Your main advice should be founded on Eve Online universe but can be extended with general adivce. Your style is ironic, hyperoptimistic and with an urge to praise the beautiful explosions that happen in this game.

Previous conversation for user {user_name}:
{history}

User: {user_input}
Chatbot: """

prompt = PromptTemplate(input_variables=["history", "user_input", "user_name"], template=template)


# Load conversation history from the database
def load_conversation_history(user_name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_input, chatbot_response FROM conversations WHERE user_name = ? ORDER BY id ASC",
                   (user_name,))
    results = cursor.fetchall()
    history_str = ""
    for user_input, chatbot_response in results:
        history_str += f"User: {user_input}\nChatbot: {chatbot_response}\n"
    return history_str


# Function to handle user input and generate chatbot responses
def get_chatbot_response(user_input, conversation_history, user_name):
    # Format the prompt using the template and the history
    formatted_prompt = prompt.format(history=conversation_history, user_input=user_input, user_name=user_name)

    response = model.generate_content(formatted_prompt).text

    return response


@app.route("/", methods=["GET", "POST"])
def chat():
    user_name = request.args.get("user_name")
    if user_name is None:
        return redirect(url_for('get_user_name'))  # redirects to get_user_name if there is no user_name

    conversation_history = load_conversation_history(user_name)

    if request.method == "POST":
        user_input = request.form["user_input"]
        chatbot_response = get_chatbot_response(user_input, conversation_history, user_name)

        # Save the conversation to the database, including the name
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_name, user_input, chatbot_response) VALUES (?, ?, ?)",
            (user_name, user_input, chatbot_response),
        )
        db.commit()

        conversation_history += f"User: {user_input}\nChatbot: {chatbot_response}\n"

        return render_template("index.html", user_name=user_name, conversation_history=conversation_history,
                               chatbot_response=chatbot_response)

    return render_template("index.html", user_name=user_name, conversation_history=conversation_history,
                           chatbot_response=None)


@app.route("/get_user_name", methods=["GET", "POST"])  # Route for getting the user name
def get_user_name():
    if request.method == "POST":
        user_name = request.form["user_name"]
        return redirect(url_for("chat", user_name=user_name))  # Redirect to chat with user name
    return render_template("get_user_name.html")

@app.route("/history/<user_name>")
def show_conversation_history(user_name):
    conversation_history = load_conversation_history(user_name)
    return render_template("history.html", user_name=user_name, conversation_history=conversation_history)


if __name__ == "__main__":
    app.run(debug=True)  # Remove debug=True for production