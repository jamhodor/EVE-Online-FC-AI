import sqlite3

DB_FILE = "chatbot_conversation.db"  # Database file

def get_conversation_history(user_name):
    """Retrieves the conversation history for a specific user from the database.

    Args:
        user_name (str): The name of the user.

    Returns:
        list: A list of tuples, where each tuple contains (user_input, chatbot_response)
              for a single turn in the conversation.  Returns an empty list if no history is found.
    """

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT user_input, chatbot_response FROM conversations WHERE user_name = ? ORDER BY id ASC", (user_name,))
        results = cursor.fetchall()

        return results  # Return the list of tuples

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []  # Return an empty list in case of an error

    finally:
        if conn:  # Ensure connection is closed even if there's an exception
            conn.close()

if __name__ == "__main__":
    user_name_to_retrieve = input("Enter the user name to retrieve conversation history: ")

    history = get_conversation_history(user_name_to_retrieve)

    if history:
        print(f"\nConversation History for User: {user_name_to_retrieve}\n")
        for user_input, chatbot_response in history:
            print(f"User: {user_input}")
            print(f"Chatbot: {chatbot_response}")
            print("-" * 20)  # Separator
    else:
        print(f"No conversation history found for user: {user_name_to_retrieve}")