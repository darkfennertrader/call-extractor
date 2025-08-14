"""
FastMCP Server with Webhook/Callback Pattern
Clients register callback URLs and receive HTTP POST notifications when tasks complete
"""

import time
import importlib  # For dynamic imports
import pkgutil  # For iterating over modules in a package
import uvicorn  # ASGI server for running the app
from fastmcp import FastMCP  # Main FastMCP server class
from starlette.requests import Request  # HTTP request object
from starlette.responses import JSONResponse  # For JSON HTTP responses
import tools  # Tools package containing custom tool modules


# Automatic discovery and registration of tools

from tools.shared_state import task_results, task_callbacks

# Create the FastMCP server instance
mcp = FastMCP("AsyncFastMCPServer")

# Dynamically import and register all tools in the tools/ directory
# This allows for modular tool development: any module in tools/ with a register_tools(mcp) function will be registered
for _, module_name, _ in pkgutil.iter_modules(tools.__path__):
    module = importlib.import_module(f"tools.{module_name}")
    if hasattr(module, "register_tools"):
        module.register_tools(mcp)


# Webhook receiver endpoint (for testing)
@mcp.custom_route("/webhook/{client_id}", methods=["POST"])
async def receive_webhook(request: Request):
    """
    Test webhook endpoint that clients can use to receive callbacks.
    In real scenarios, clients would have their own webhook endpoints.
    """
    # Extract client_id from the URL path
    client_id = request.path_params["client_id"]

    try:
        # Parse the JSON payload sent to the webhook
        payload = await request.json()

        # Log the webhook receipt for debugging/monitoring
        print(
            f"🎯 Webhook received for {client_id}: {payload['type']} - {payload['task_id']}"
        )

        # Store the received webhook for inspection (could be extended to persist in a DB)
        webhook_log = {
            "received_at": time.time(),
            "client_id": client_id,
            "payload": payload,
        }

        # You could store this in a database or return it via another tool

        # Respond to the sender confirming receipt
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
        # Handle errors in payload parsing or processing
        print(f"❌ Webhook error for {client_id}: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)}, status_code=400
        )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for monitoring server status"""

    # Count total pending callbacks across all tasks
    total_callbacks = sum(
        len(callbacks) for callbacks in task_callbacks.values()
    )

    # Return server health and status metrics
    return JSONResponse(
        {
            "status": "healthy",
            "server": "AsyncFastMCP Server with Webhook Callbacks",
            "transport": "HTTP with Webhook Callbacks",
            "completed_tasks": len(task_results),
            "pending_callbacks": total_callbacks,
            "active_tasks": len(task_callbacks),
            "timestamp": time.time(),
        }
    )


if __name__ == "__main__":
    # Print startup information and available endpoints/tools
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

    # Create the ASGI app from the FastMCP server
    app = mcp.http_app()
    # Configure uvicorn to disable websockets and use only HTTP/1.1 (h11)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8011,
        log_level="info",
        ws="none",  # Disable websockets completely
        http="h11",  # Use only HTTP/1.1 with h11
    )
