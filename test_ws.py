import asyncio
import websockets

async def test():
    uri = "ws://127.0.0.1:8000/ws/chat"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await websocket.send('{"type":"ping"}')
            response = await websocket.recv()
            print(f"Received: {response}")
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test())
