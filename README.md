# Chat app project

## Server
Implement a service that processes incoming requests from clients.

**Conditions and requirements:**

- A connected client is added to the "general" chat, where previously connected clients are located.
- After connecting, the latest N messages from the general chat are available to a new client (20 by default).
- A reconnected client has the ability to view all previously unread messages until the moment of the last poll (both from the general chat and private ones).
- By default, the server starts on the local host (127.0.0.1) and on port 8000 (the ability to specify any).


## Client
Implement a service that can connect to the server to exchange messages with other clients.

**Conditions and requirements:**

- After connecting, the client can send messages to the "general" chat.
- Ability to send a message in a private chat (1-to-1) to any participant from the general chat.


## Server Installation

1. **Clone the Repository**
   ```
   git clone git@github.com:dmshirochenko/async-python-sprint-3.git
   ```
2. **To Start the Server**
   ```
   make start
   ```
3. **To Stop the Server**
   ```
   make stop
   ```
4. **To Run the Client**
   ```
   python client.py
   ```


## Endpoint Descriptions for HTTPProtocol

## GET Endpoints

### Path: /status
- **Method:** `GET`
- **Parameters:**
  - URL Query Parameters: Optional parameters for filtering or specifying the status request.
  - `token`: Authorization token (extracted from request headers).

### Path: /health
- **Method:** `GET`
- **Parameters:** None

## POST Endpoints

### Path: /connect
- **Method:** `POST`
- **Parameters:** None

### Path: /send
- **Method:** `POST`
- **Parameters:**
  - `request_body`: JSON payload containing the message text.
  - `token`: Authorization token (extracted from request headers).

### Path: /send-private
- **Method:** `POST`
- **Parameters:**
  - `request_body`: JSON payload containing the message text and recipient's user ID.
  - `token`: Authorization token (extracted from request headers).

