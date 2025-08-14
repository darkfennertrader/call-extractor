"""
Callback-related tools and helpers for FastMCP server.
"""

import time
import asyncio
from fastmcp import FastMCP
import httpx

from .shared_state import task_results, task_callbacks


def register_tools(mcp: FastMCP):
    @mcp.tool
    async def register_callback(
        task_id: str, client_id: str, callback_url: str
    ) -> dict:
        """
        Register a callback URL to receive notifications when a task completes.
        """
        print(
            f"📞 Registering callback for client {client_id} on task {task_id}"
        )

        callback_info = {
            "client_id": client_id,
            "callback_url": callback_url,
            "registered_at": time.time(),
        }

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
        """
        print(f"🔄 Starting callback task {task_id} for client {client_id}")

        callback_count = len(task_callbacks.get(task_id, []))
        asyncio.create_task(process_callback_task(task_id, client_id))

        return {
            "status": "started",
            "task_id": task_id,
            "client_id": client_id,
            "message": f"🚀 Task started! Will notify {callback_count} registered callbacks when complete.",
            "registered_callbacks": callback_count,
            "timestamp": time.time(),
        }

    @mcp.tool
    async def get_registered_callbacks(task_id: str) -> dict:
        """
        Get list of registered callbacks for a task.
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

    # Helper functions (not tools)
    async def process_callback_task(task_id: str, client_id: str):
        """Process task and send callbacks when complete"""
        try:
            print(f"🔨 Processing callback task {task_id}...")

            await asyncio.sleep(10)

            result = f"Task {task_id} completed successfully with data: [processed_data_123]"
            task_results[task_id] = result

            print(f"✅ Task {task_id} completed, sending callbacks...")

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

        async with httpx.AsyncClient(timeout=30.0) as client:
            for callback_info in callbacks:
                try:
                    callback_url = callback_info["callback_url"]
                    client_id = callback_info["client_id"]

                    callback_payload = {
                        **payload,
                        "callback_client_id": client_id,
                        "callback_sent_at": time.time(),
                    }

                    print(
                        f"📤 Sending callback to {client_id} at {callback_url}"
                    )

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

        if task_id in task_callbacks:
            del task_callbacks[task_id]
