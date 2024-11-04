import asyncio
from websockets.asyncio.server import serve

async def handler(websocket):
    await websocket.open()
    name = await websocket.recv()
    print(f"<<< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f">>> {greeting}")

async def main():
    async with serve(handler, "127.0.0.1", 4000):
        await asyncio.get_running_loop().create_future()

asyncio.run(main())