"""
FastMCP Server with Webhook/Callback Pattern
Clients register callback URLs and receive HTTP POST notifications when tasks complete
"""

import asyncio
import json
import time
from typing import Dict, Any, List
import httpx

import uvicorn
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Create FastMCP server
mcp = FastMCP("TrovabandoServer")

# Store task results and registered callbacks
task_results: Dict[str, str] = {}
task_callbacks: Dict[str, List[Dict]] = (
    {}
)  # task_id -> list of callback registrations


@mcp.tool
async def register_callback(
    task_id: str, client_id: str, callback_url: str
) -> dict:
    """
    Register a callback URL to receive notifications when a task completes.

    Args:
        task_id: Task ID to monitor
        client_id: Your client identifier
        callback_url: HTTP endpoint where you want to receive the result

    Returns:
        Registration confirmation
    """
    print(f"📞 Registering callback for client {client_id} on task {task_id}")

    # Create callback registration
    callback_info = {
        "client_id": client_id,
        "callback_url": callback_url,
        "registered_at": time.time(),
    }

    # Store the callback
    if task_id not in task_callbacks:
        task_callbacks[task_id] = []

    task_callbacks[task_id].append(callback_info)

    return {
        "status": "registered",
        "task_id": task_id,
        "client_id": client_id,
        "callback_url": callback_url,
        "message": f"✅ Callback registered! You'll receive HTTP POST to {callback_url} when task {task_id} completes.",
        "registered_callbacks": len(task_callbacks[task_id]),
        "timestamp": time.time(),
    }


@mcp.tool
async def start_task_with_callbacks(task_id: str, client_id: str) -> dict:
    """
    Start a task that will notify all registered callbacks when complete.

    Args:
        task_id: Unique identifier for the task
        client_id: Client identifier who started the task

    Returns:
        Task start confirmation
    """
    print(f"🔄 Starting callback task {task_id} for client {client_id}")

    # Check how many callbacks are registered
    callback_count = len(task_callbacks.get(task_id, []))

    # Start the background task
    asyncio.create_task(process_callback_task(task_id, client_id))

    return {
        "status": "started",
        "task_id": task_id,
        "client_id": client_id,
        "message": f"🚀 Task started! Will notify {callback_count} registered callbacks when complete.",
        "registered_callbacks": callback_count,
        "processing_time": "~10 seconds",
        "timestamp": time.time(),
    }


@mcp.tool
async def get_registered_callbacks(task_id: str) -> dict:
    """
    Get list of registered callbacks for a task.

    Args:
        task_id: Task ID to check

    Returns:
        List of registered callbacks
    """
    callbacks = task_callbacks.get(task_id, [])

    return {
        "task_id": task_id,
        "callback_count": len(callbacks),
        "callbacks": [
            {
                "client_id": cb["client_id"],
                "callback_url": cb["callback_url"],
                "registered_at": cb["registered_at"],
            }
            for cb in callbacks
        ],
        "timestamp": time.time(),
    }


@mcp.tool
async def get_task_result(task_id: str) -> dict:
    """Get task result if completed (backup method)"""
    if task_id in task_results:
        return {
            "task_id": task_id,
            "status": "completed",
            "result": task_results[task_id],
            "message": "✅ Task completed!",
            "timestamp": time.time(),
        }
    else:
        return {
            "task_id": task_id,
            "status": "not_found_or_pending",
            "result": None,
            "message": "⏳ Task not found or still processing",
            "timestamp": time.time(),
        }


async def process_callback_task(task_id: str, client_id: str):
    """Process task and send callbacks when complete"""
    try:
        print(f"🔨 Processing callback task {task_id}...")

        # Simulate work
        await asyncio.sleep(10)

        # Complete the task
        result = f"Task {task_id} completed successfully with data: [processed_data_123]"
        task_results[task_id] = result

        print(f"✅ Task {task_id} completed, sending callbacks...")

        # Send callbacks to all registered clients
        await send_callbacks(
            task_id,
            {
                "type": "task_completed",
                "task_id": task_id,
                "started_by": client_id,
                "result": result,
                "message": "🎉 Task completed successfully!",
                "completion_time": time.time(),
            },
        )

        print(f"📞 All callbacks sent for task {task_id}")

    except Exception as e:
        # Send error callbacks
        await send_callbacks(
            task_id,
            {
                "type": "task_failed",
                "task_id": task_id,
                "started_by": client_id,
                "error": str(e),
                "message": "❌ Task failed",
                "completion_time": time.time(),
            },
        )
        print(f"❌ Task {task_id} failed: {e}")


async def send_callbacks(task_id: str, payload: dict):
    """Send HTTP POST callbacks to all registered URLs"""
    if task_id not in task_callbacks:
        print(f"⚠️ No callbacks registered for task {task_id}")
        return

    callbacks = task_callbacks[task_id]
    print(f"📞 Sending {len(callbacks)} callbacks for task {task_id}")

    # Send to all registered callbacks
    async with httpx.AsyncClient(timeout=30.0) as client:
        for callback_info in callbacks:
            try:
                callback_url = callback_info["callback_url"]
                client_id = callback_info["client_id"]

                # Add client info to payload
                callback_payload = {
                    **payload,
                    "callback_client_id": client_id,
                    "callback_sent_at": time.time(),
                }

                print(f"📤 Sending callback to {client_id} at {callback_url}")

                # Send HTTP POST
                response = await client.post(
                    callback_url,
                    json=callback_payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    print(f"✅ Callback delivered to {client_id}")
                else:
                    print(
                        f"⚠️ Callback to {client_id} returned status {response.status_code}"
                    )

            except Exception as e:
                print(
                    f"❌ Failed to send callback to {callback_info['client_id']}: {e}"
                )

    # Clean up callbacks after sending
    if task_id in task_callbacks:
        del task_callbacks[task_id]


# Webhook receiver endpoint (for testing)
@mcp.custom_route("/webhook/{client_id}", methods=["POST"])
async def receive_webhook(request: Request):
    """
    Test webhook endpoint that clients can use to receive callbacks.
    In real scenarios, clients would have their own webhook endpoints.
    """
    client_id = request.path_params["client_id"]

    try:
        payload = await request.json()

        print(
            f"🎯 Webhook received for {client_id}: {payload['type']} - {payload['task_id']}"
        )

        # Store the received webhook for inspection
        webhook_log = {
            "received_at": time.time(),
            "client_id": client_id,
            "payload": payload,
        }

        # You could store this in a database or return it via another tool

        return JSONResponse(
            {
                "status": "received",
                "client_id": client_id,
                "task_id": payload.get("task_id"),
                "message": f"✅ Webhook received by {client_id}",
                "timestamp": time.time(),
            }
        )

    except Exception as e:
        print(f"❌ Webhook error for {client_id}: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)}, status_code=400
        )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint"""
    total_callbacks = sum(
        len(callbacks) for callbacks in task_callbacks.values()
    )

    return JSONResponse(
        {
            "status": "healthy",
            "server": "FastMCP TrovabandoServer - Webhook Callbacks",
            "transport": "HTTP with Webhook Callbacks",
            "completed_tasks": len(task_results),
            "pending_callbacks": total_callbacks,
            "active_tasks": len(task_callbacks),
            "timestamp": time.time(),
        }
    )


if __name__ == "__main__":
    print("🚀 Starting FastMCP Server with Webhook Callbacks")
    print("📡 MCP endpoint: http://localhost:8011/mcp/")
    print("🪝 Test webhook: http://localhost:8011/webhook/{client_id}")
    print("🏥 Health check: http://localhost:8011/health")
    print("")
    print("🎯 Tools Available:")
    print(
        "   1. register_callback - Register webhook URL to receive task results"
    )
    print(
        "   2. start_task_with_callbacks - Start task and notify all registered callbacks"
    )
    print(
        "   3. get_registered_callbacks - View registered callbacks for a task"
    )
    print("   4. get_task_result - Get task result (backup method)")
    print("")
    print("📞 Workflow:")
    print("   Inspector B: register_callback(task_id, client_id, webhook_url)")
    print("   Inspector A: start_task_with_callbacks(task_id, client_id)")
    print("   Server: Automatically sends HTTP POST to Inspector B's webhook")

    app = mcp.http_app()
    # Configure uvicorn to disable websockets and use only HTTP
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8011,
        log_level="info",
        ws="none",  # Disable websockets completely
        http="h11",  # Use only HTTP/1.1 with h11
    )
