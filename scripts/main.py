import json
import asyncio
import base64
import requests

from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import DataReader, InputStreamOptions
from typing import TypedDict


class MediaInfo(TypedDict):
    meta: dict[str, str | None]
    json: str


async def get_media_info(session):
    info = await session.try_get_media_properties_async()
    # Извлечение информации о текущем треке
    artist = info.artist
    title = info.title

    # Извлечение обложки
    thumb = info.thumbnail
    album_art_base64 = None
    if thumb:
        stream = await thumb.open_read_async()
        size = stream.size
        data_reader = DataReader(stream)
        await data_reader.load_async(size)
        buffer = data_reader.read_buffer(size)
        data = bytearray(buffer.length)
        data_reader.read_bytes(data)
        album_art_base64 = base64.b64encode(data).decode('utf-8')

    meta = {
        "artist": artist,
        "title": title,
        "album_art_base64": album_art_base64
    }
    return MediaInfo(meta=meta, json=json.dumps(meta))


async def session_changed_handler(sender, args):
    print("Current session has changed!")
    session = sender.get_current_session()
    if session:
        previous_json_data = None

        media_info = await get_media_info(session)
        json_data = media_info.get('json')

        if json_data != previous_json_data:
            previous_json_data = json_data
            send_data(media_info.get('meta'))

        await asyncio.sleep(1)
    else:
        print("No active media session.")


async def media_info_observer():
    manager = await MediaManager.request_async()

    print("Start current media session observation")
    manager.add_current_session_changed(session_changed_handler)

    while True:
        await asyncio.sleep(1)


def send_data(data):
    print(data)


if __name__ == "__main__":
    asyncio.run(media_info_observer())
