"""
Client Webhook Receiver

This HTTP server receives POST callbacks from the MCP server when a task completes.
It listens on /webhook/{client_id} and prints the received payload.
"""

import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn


app = FastAPI()


@app.post("/webhook/{client_id}")
async def receive_webhook(client_id: str, request: Request):
    try:
        payload = await request.json()
        print(
            f"🎯 Webhook received for {client_id}: {payload.get('type')} - {payload.get('task_id')}"
        )
        print(f"Payload: {payload}")
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


if __name__ == "__main__":
    print(
        "🚀 Starting Client Webhook Receiver on http://localhost:9000/webhook/{client_id}"
    )
    uvicorn.run(app, host="0.0.0.0", port=9000)
