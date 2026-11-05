import json
import asyncio
import websockets

async def simulate_telemetry():
    uri = "ws://localhost:5000/ws/telemetry"

    payload = {
        "equipment_id": 1,
        "member_id": 2,
        "nps": 8.5
    }

    async with websockets.connect(uri) as websocket:
        print(f"Sending telemetry: {json.dumps(payload)}")
        await websocket.send(json.dumps(payload))

        response = await websocket.recv()
        print(f"Received handshake: {response}")

if __name__ == "__main__":
    asyncio.run(simulate_telemetry())
