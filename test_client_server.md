# Testing the Client-Server Structure (MCP Server, Client Webhook Receiver, and Client)

This guide explains how to test the full workflow of the MCP server, client webhook receiver, and client agent in this project.

---

## Prerequisites

- Python 3.12+ installed
- [uv](https://github.com/astral-sh/uv) installed (recommended for fast dependency management)
  ```bash
  pip install uv
  ```
- All dependencies installed:
  ```bash
  uv pip install -r requirements.txt
  ```
- (Optional but recommended) Use a virtual environment:
  ```bash
  uv venv .venv
  source .venv/bin/activate
  ```

---

## Step 1: Start the MCP Server

Open a terminal and run:

```bash
uv run webhook_callback_server.py
```

- The server will start on `http://localhost:8011/mcp/`.
- You should see logs indicating the server is running and available endpoints.

---

## Step 2: Start the Client Webhook Receiver

Open a **second terminal** and run:

```bash
uv run client_webhook_receiver.py
```

- This starts a FastAPI server on `http://localhost:9000/webhook/{client_id}`.
- The receiver will print any callback payloads it receives.

---

## Step 3: Run the Client Agent

Open a **third terminal** and run:

```bash
uv run client.py
```

- The client will:
  - Register a callback with the MCP server
  - Start a task (the default task is a simulated sleep)
  - Wait for the callback (the webhook receiver will print the payload when the task completes)
  - Show the workflow step by step in the terminal

---

## What to Expect

- **MCP Server Terminal:** Logs for callback registration, task processing, and callback delivery.
- **Webhook Receiver Terminal:** Prints the received callback payload when the task completes (after ~10 seconds).
- **Client Terminal:** Shows the workflow progress and completion.

---

## Example Output

**Client Terminal:**
```
🤖 Starting LangGraph Agent for Call Extractor MCP Server
📋 Task ID: task_xxxxxxxx
👤 Client ID: client_yyyyyyyy
🔄 Callback URL: http://localhost:9000/webhook/client_yyyyyyyy
----------------------------------------------
🔵 User: I want to use the webhook callback server to process a task...
🤖 Agent: Here’s a step-by-step workflow...
🔧 Tool (register_callback): Callback registered!
🔧 Tool (start_task_with_callbacks): Task started!
...
✅ Workflow completed!
```

**Webhook Receiver Terminal:**
```
🎯 Webhook received for client_yyyyyyyy: task_completed - task_xxxxxxxx
Payload: {...}
```

---

## Troubleshooting

- If the client fails to connect, ensure the MCP server is running at `http://localhost:8011/mcp/`.
- If you see "StructuredTool does not support sync invocation", ensure you are using async streaming in `client.py`.
- Make sure all dependencies are installed and you are using the correct Python environment (created with `uv venv`).

---

## Summary

You need three terminals:
1. Run the MCP server (`uv run webhook_callback_server.py`)
2. Run the webhook receiver (`uv run client_webhook_receiver.py`)
3. Run the client (`uv run client.py`)

This setup tests the full client-server workflow, including callback registration, task execution, and webhook notification.
