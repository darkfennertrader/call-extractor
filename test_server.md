# FastMCP Webhook Callback Server - Test Guide

## 🎯 Overview

This guide demonstrates how to test the **webhook/callback pattern** using the FastMCP server. The pattern allows clients to register webhook URLs and receive HTTP POST notifications when tasks complete, eliminating the need for polling.

## 🚀 Prerequisites

- FastMCP server running on port 8011
- MCP Inspector available 
- Two browser tabs for testing

## 📋 Test Setup

### Step 1: Start the Webhook Callback Server

```bash
# Navigate to project directory
cd /home/ray/projects/trovabando

# Activate virtual environment
source .venv/bin/activate

# Start the webhook callback server
uv run python webhook_callback_server.py
```

**Expected Output:**
```
🚀 Starting FastMCP Server with Webhook Callbacks
📡 MCP endpoint: http://localhost:8011/mcp/
🪝 Test webhook: http://localhost:8011/webhook/{client_id}
🏥 Health check: http://localhost:8011/health
```

### Step 2: Start MCP Inspector

```bash
# In a new terminal
cd /home/ray/projects/trovabando
DANGEROUSLY_OMIT_AUTH=true PORT=6274 npx @modelcontextprotocol/inspector
```

**Expected Output:**
```
🔍 MCP Inspector is up and running at http://127.0.0.1:6274 🚀
```

### Step 3: Open Two Inspector Tabs

1. **Tab 1 (Inspector B - Receiver):** Open `http://localhost:6274`
2. **Tab 2 (Inspector A - Sender):** Open `http://localhost:6274` in a new tab

**Both tabs should connect to:** `http://localhost:8011/mcp/`

## 🧪 Test Execution

### Phase 1: Register Webhook Callback

**In Tab 1 (Inspector B):**

```
Tool: register_callback
Parameters:
- task_id: demo_task_123
- client_id: inspector_b
- callback_url: http://localhost:8011/webhook/inspector_b
```

**Expected Response:**
```json
{
  "status": "registered",
  "task_id": "demo_task_123",
  "client_id": "inspector_b",
  "callback_url": "http://localhost:8011/webhook/inspector_b",
  "message": "✅ Callback registered! You'll receive HTTP POST to http://localhost:8011/webhook/inspector_b when task demo_task_123 completes.",
  "registered_callbacks": 1,
  "timestamp": [current_time]
}
```

### Phase 2: Start Task with Callbacks

**In Tab 2 (Inspector A):**

```
Tool: start_task_with_callbacks
Parameters:
- task_id: demo_task_123
- client_id: inspector_a
```

**Expected Response:**
```json
{
  "status": "started",
  "task_id": "demo_task_123",
  "client_id": "inspector_a",
  "message": "🚀 Task started! Will notify 1 registered callbacks when complete.",
  "registered_callbacks": 1,
  "processing_time": "~10 seconds",
  "timestamp": [current_time]
}
```

### Phase 3: Monitor Webhook Delivery

**Watch the server terminal for these logs:**

```
🔨 Processing callback task demo_task_123...
✅ Task demo_task_123 completed, sending callbacks...
📞 Sending 1 callbacks for task demo_task_123
📤 Sending callback to inspector_b at http://localhost:8011/webhook/inspector_b
🎯 Webhook received for inspector_b: task_completed - demo_task_123
INFO:     127.0.0.1:49760 - "POST /webhook/inspector_b HTTP/1.1" 200 OK
✅ Callback delivered to inspector_b
📞 All callbacks sent for demo_task_123
```

### Phase 4: Verify Task Result

**In either inspector tab:**

```
Tool: get_task_result
Parameters:
- task_id: demo_task_123
```

**Expected Response:**
```json
{
  "task_id": "demo_task_123",
  "status": "completed",
  "result": "Task demo_task_123 completed successfully with data: [processed_data_123]",
  "message": "✅ Task completed!",
  "timestamp": [current_time]
}
```

## 🔍 Additional Test Tools

### Check Registered Callbacks

```
Tool: get_registered_callbacks
Parameters:
- task_id: demo_task_123
```

### Health Check

**Browser:** `http://localhost:8011/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "server": "FastMCP TrovabandoServer - Webhook Callbacks",
  "transport": "HTTP with Webhook Callbacks",
  "completed_tasks": 1,
  "pending_callbacks": 0,
  "active_tasks": 0,
  "timestamp": [current_time]
}
```

## ✅ Success Criteria

1. **Registration Success:** Tab 1 receives confirmation of webhook registration
2. **Task Start Success:** Tab 2 receives confirmation of task start
3. **Webhook Delivery:** Server logs show successful HTTP POST to webhook
4. **Result Retrieval:** Either tab can retrieve the completed task result
5. **No Polling Required:** Results delivered via push notifications, not polling

## 🎯 Test Workflow Summary

```
Inspector B → register_callback(task_id, client_id, webhook_url)
Inspector A → start_task_with_callbacks(task_id, client_id)
Server → [processes task for 10 seconds]
Server → [sends HTTP POST to Inspector B's webhook automatically]
Either Inspector → get_task_result(task_id) [optional verification]
```

## 🏆 Key Benefits Demonstrated

- ✅ **No Polling** - Clients receive push notifications via HTTP POST
- ✅ **Multiple Callbacks** - Multiple clients can register for the same task
- ✅ **Scalable** - No persistent connections required
- ✅ **Standard HTTP** - Uses proven webhook pattern
- ✅ **Reliable** - Automatic retry and error handling

## 🐛 Troubleshooting

### Server Not Starting
- Check if port 8011 is available: `lsof -i :8011`
- Ensure httpx is installed: `uv add httpx`

### Inspector Connection Issues
- Verify server is running: `curl http://localhost:8011/health`
- Check inspector URL: `http://localhost:6274`
- Ensure both tabs connect to: `http://localhost:8011/mcp/`

### No Webhook Delivery
- Check server logs for error messages
- Verify callback URL is accessible
- Ensure task_id matches between registration and start

### Tool Not Found
- Confirm inspector is connected to port 8011, not 8001 or 8002
- Refresh inspector page and reconnect

## 📊 Test Variations

### Test Multiple Callbacks
Register multiple clients for the same task:

**Tab 1:**
```
register_callback(task_id="multi_test", client_id="client_1", callback_url="http://localhost:8011/webhook/client_1")
```

**Tab 2:**
```
register_callback(task_id="multi_test", client_id="client_2", callback_url="http://localhost:8011/webhook/client_2")
```

**Tab 1:**
```
start_task_with_callbacks(task_id="multi_test", client_id="sender")
```

Both clients will receive webhooks simultaneously!

---

## 🎉 Congratulations!

You've successfully implemented and tested a **webhook-based notification system** using FastMCP! This pattern is production-ready and scalable for real-world applications.
