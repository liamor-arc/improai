import logging
import json
import asyncio
from .EventHandler import EventHandler
from websockets.asyncio.server import serve

class WebSocket:
    def __init__(self, host, port):
        self.eventHandler = EventHandler()
        self.connection = serve(self.handler, host, port)
        self.connected_clients = []
    
    async def handler(self, websocket):
        self.connected_clients.append(websocket)
        async for message in websocket:
            logging.info(f"Websocket Request: ${message}")
            print(f"<<< {message}")
            request = json.loads(message)
            self.eventHandler.emit("json", request)
        print("Closed connection")
        self.connected_clients.remove(websocket)
    
    async def sendAsync(self, websocket, payload):
        print("send async")
        await websocket.send(json.dumps(payload))
        
    def onJSON(self, callback):
        self.eventHandler.addEventHandler("json", callback)
        
    def sendToAll(self, payload):
        print("send all")
        for websocket in self.connected_clients:
            coroutine = self.sendAsync(websocket, payload)
            try:
                asyncio.get_running_loop().create_task(coroutine)
            except:
                asyncio.run(coroutine)
            
    async def __aenter__(self):
        await self.connection.__aenter__()
        return self
    
    async def __aexit__(self, *args, **kwargs):
        return await self.connection.__aexit__(*args, **kwargs)
