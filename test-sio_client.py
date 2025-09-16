import asyncio

import socketio


sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("Connected to Backend")
    await sio.send("Hello from worker!")


@sio.event
async def disconnect():
    print("Disconnected from server")
    await sio.sleep(1)


async def main():
    await sio.connect("http://127.0.0.1:5000")
    await asyncio.sleep(1)
    await sio.send({"data": "Hello from worker!"})
    await sio.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
