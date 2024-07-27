import websockets


async def process_request(websocket: websockets.WebSocketServerProtocol, message: str):
    if message == "hello":
        await websocket.send("Hello there!")
    elif message == "bye":
        await websocket.send("Goodbye!")
    else:
        await websocket.send("Don't know how to respond...")