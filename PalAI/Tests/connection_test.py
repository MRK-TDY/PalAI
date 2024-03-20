import asyncio
import socketio

# Create a Socket.IO client
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connection established')

@sio.event
async def disconnect():
    print('Disconnected from server')

@sio.event
async def build_response(data):
    print('Build Response:', data)

@sio.event
async def layer(data):
    print('Layer Data:', data)

@sio.event
async def material(data):
    print('Material Data:', data)

@sio.event
async def add_ons(data):
    print('Add-ons Data:', data)

async def send_build_request():
    await sio.connect('http://localhost:8000')
    await sio.emit('build', {'prompt': 'I want a small building'})
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(send_build_request())

