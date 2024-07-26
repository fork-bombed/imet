import asyncio
import websockets

async def client():
    uri = "ws://localhost:8765"  # Replace with the actual IP address
    async with websockets.connect(uri) as websocket:
        command = input("> ")
        await websocket.send(command)
        print(f"Sent command: {command}")

        response = await websocket.recv()
        print(f"Received response: {response}")

asyncio.get_event_loop().run_until_complete(client())