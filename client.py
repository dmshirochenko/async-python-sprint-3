import requests

SERVER_URL = "http://127.0.0.1:8000"


def get_chat_history():
    response = requests.get(SERVER_URL)
    if response.status_code == 200:
        # print("Chat History:")
        print(response.text)
    else:
        print("Failed to retrieve chat history.")


def post_message():
    message = input("Enter your message: ")
    response = requests.post(SERVER_URL, data=message)
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print("Failed to send message.")


def main():
    while True:
        action = input("Choose an action: 'get' to view chat history, 'post' to send a message, 'quit' to exit: ")
        if action.lower() == "get":
            get_chat_history()
        elif action.lower() == "post":
            post_message()
        elif action.lower() == "quit":
            break
        else:
            print("Invalid action. Please choose 'get', 'post', or 'quit'.")


if __name__ == "__main__":
    main()
