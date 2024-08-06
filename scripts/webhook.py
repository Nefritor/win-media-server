import asyncio
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)

# Глобальная переменная для хранения цикла событий
event_loop = None


async def session_changed_handler(sender, args):
    print("Current session has changed!")
    session = sender.get_current_session()
    if session:
        media_properties = await session.try_get_media_properties_async()
        artist = media_properties.artist
        title = media_properties.title
        print(f"Now playing: {artist} - {title}")
    else:
        print("No active media session.")


def session_changed_callback(sender, args):
    # Используем глобальный цикл событий
    asyncio.run_coroutine_threadsafe(session_changed_handler(sender, args), event_loop)


async def main():
    global event_loop
    event_loop = asyncio.get_running_loop()

    # Получаем менеджер медиа сессий
    manager = await MediaManager.request_async()

    # Добавляем обработчик изменения текущей сессии
    manager.add_current_session_changed(session_changed_callback)

    # Чтобы не завершать программу сразу, нужно запустить бесконечный цикл
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    # Создаем новый цикл событий и запускаем основную функцию
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
