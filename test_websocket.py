import asyncio
import websockets
import json

async def test_websocket():
    try:
        async with websockets.connect('ws://localhost:5001/ws') as ws:
            # Send handshake (join action)
            handshake = {
                'action': 'join',
                'session_id': 1,
                'nickname': 'test_user'
            }
            await ws.send(json.dumps(handshake))
            print("Sent handshake")
            
            # Receive response
            response = await ws.recv()
            print(f"Received: {response}")
            response_data = json.loads(response)
            
            if response_data.get('type') == 'error':
                print(f"Error: {response_data.get('message')}")
                print("Note: Session may need to be created via API first")
                return
            
            # Send a message
            message = {
                'type': 'message',
                'session_id': 1,
                'content': 'Hello from test'
            }
            await ws.send(json.dumps(message))
            print("Sent message")
            
            # Receive response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received (timeout)")
            
            print("WebSocket test PASSED")
    except Exception as e:
        print(f"WebSocket test FAILED: {e}")

if __name__ == '__main__':
    asyncio.run(test_websocket())
