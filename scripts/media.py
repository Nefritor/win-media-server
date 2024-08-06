import base64
import asyncio
import json

import websockets

from PIL import Image
from io import BytesIO

from websockets import WebSocketServerProtocol
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import DataReader

info_dump_memo: str | None = None
connected_clients: set[WebSocketServerProtocol] = set()


def get_average_color_hex(base64_string):
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    image = image.convert('RGB')
    pixels = list(image.getdata())
    num_pixels = len(pixels)
    avg_color = tuple(sum(channel) // num_pixels for channel in zip(*pixels))
    avg_color_hex = '#{:02x}{:02x}{:02x}'.format(*avg_color)
    return avg_color_hex


async def get_media_info():
    media_manager = await MediaManager.request_async()
    current_session = media_manager.get_current_session()
    if current_session:
        media_properties = await current_session.try_get_media_properties_async()
        info = {
            'title': media_properties.title,
            'artist': media_properties.artist,
        }

        thumb = media_properties.thumbnail
        if thumb:
            stream = await thumb.open_read_async()
            size = stream.size
            data_reader = DataReader(stream)
            await data_reader.load_async(size)
            data = data_reader.read_buffer(size)
            album_art_base64 = base64.b64encode(data).decode('utf-8')

            info['album_art_base64'] = album_art_base64
            info['album_art_avg'] = get_average_color_hex(album_art_base64)

        return info
    else:
        return None


async def echo(websocket: WebSocketServerProtocol, path: str):
    connected_clients.add(websocket)
    print('Client connected to ' + path)
    try:
        await websocket.send(info_dump_memo)
        await websocket.wait_closed()
    finally:
        print('Client disconnected')
        connected_clients.remove(websocket)


async def broadcast(message):
    if connected_clients:
        clients_to_remove = []
        for client in connected_clients:
            if not client.closed:
                await client.send(message)
            else:
                clients_to_remove.append(client)

        for client in clients_to_remove:
            connected_clients.remove(client)


async def close_all_connections():
    if connected_clients:
        clients_to_remove = []
        for client in connected_clients:
            if not client.closed:
                await client.close(3000)
            clients_to_remove.append(client)

        for client in clients_to_remove:
            connected_clients.remove(client)


async def media_info_observer():
    global info_dump_memo
    print("Observation starting")
    try:
        while True:
            info = await get_media_info()
            info_dump = json.dumps(info)
            if info_dump != info_dump_memo:
                if info:
                    print(info_dump)
                else:
                    print("No active media session found.")

                await send_json_data(info)
                info_dump_memo = info_dump

            await asyncio.sleep(1)
    except asyncio.exceptions.CancelledError:
        print("Observation stopped")


async def send_json_data(data):
    json_data = json.dumps(data)
    await broadcast(json_data)


async def start_app():
    await websockets.serve(echo, "localhost", 1232)
    print('Websocket server started at ws://localhost:1232')
    await media_info_observer()
    await close_all_connections()


if __name__ == "__main__":
    try:
        asyncio.run(start_app())
    finally:
        print('Application closed')
