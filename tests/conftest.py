import asyncio

import pytest
import pytest_asyncio
import socketio
from aiohttp import web
from pytest_asyncio import is_async_test

from src.app import init_app
from src.modules.mod import Riddle


# https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/run_session_tests_in_same_loop.html
def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest_asyncio.fixture(scope="session")
async def server():
    app = await init_app()
    runner = web.AppRunner(app, shutdown_timeout=3)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()
    yield site
    await asyncio.sleep(1)
    for task in asyncio.all_tasks():
        task.cancel()
    await runner.cleanup()


@pytest_asyncio.fixture(scope="session", name="sio")
async def client(server):
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)
    init_chat(sio)
    init_riddle(sio)
    init_trivia(sio)
    yield sio
    await sio.disconnect()


@pytest_asyncio.fixture(scope="session", name="conn")
async def conn(sio):
    try:
        await sio.connect(url="http://127.0.0.1:8080")
        yield sio
        await sio.disconnect()
    except socketio.exceptions.ConnectionError as err:
        print(f"Error: {err}")
        await sio.disconnect()


def idtype(val):
    if not isinstance(val, str):
        return type(val)


EXPECTED_CHAT_DATA = []
EXPECTED_RIDDLE_DATA = []
EXPECTED_TRIVIA_DATA = []


def init_chat(sio):
    @sio.on("connect", namespace="/chat")
    async def on_connect():
        EXPECTED_CHAT_DATA.append("connected")

    @sio.on("message", namespace="/chat")
    async def on_message(data):
        EXPECTED_CHAT_DATA.append(data)

    @sio.on("rooms", namespace="/chat")
    async def on_rooms(data):
        EXPECTED_CHAT_DATA.append(data)


def init_riddle(sio):
    @sio.on("connect", namespace="/riddle")
    async def on_connect():
        EXPECTED_RIDDLE_DATA.append("connected")

    @sio.on("answer", namespace="/riddle")
    async def on_answer(data):
        EXPECTED_RIDDLE_DATA.append(data)

    @sio.on("riddle", namespace="/riddle")
    async def on_riddle(data):
        EXPECTED_RIDDLE_DATA.append(data)

    @sio.on("result", namespace="/riddle")
    async def on_result(data):
        EXPECTED_RIDDLE_DATA.append(data)

    @sio.on("score", namespace="/riddle")
    async def on_score(data):
        EXPECTED_RIDDLE_DATA.append(data)


def init_trivia(sio):
    @sio.on("connect", namespace="/trivia")
    async def on_connect():
        EXPECTED_TRIVIA_DATA.append("connected")

    @sio.on("topics", namespace="/trivia")
    async def on_topics(data):
        EXPECTED_TRIVIA_DATA.append(data)

    @sio.on("game", namespace="/trivia")
    async def on_game(data):
        EXPECTED_TRIVIA_DATA.append(data)
