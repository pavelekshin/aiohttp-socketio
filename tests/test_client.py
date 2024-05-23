import asyncio

import pytest
import pytest_asyncio
import socketio
from aiohttp import web
from socketio import AsyncClient

from app import init_app
from modules.modules import Riddle

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


@pytest_asyncio.fixture(scope="session")
async def server():
    app = await init_app()
    runner = web.AppRunner(app, shutdown_timeout=3)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()
    yield site
    await asyncio.sleep(1)
    await runner.cleanup()


@pytest_asyncio.fixture(scope="session", name="sio")
async def client(server):  # noqa
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)
    init_chat(sio)
    init_riddle(sio)
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


@pytest.mark.parametrize(
    "event, data, expected",
    [
        ("connected", None, "connected"),
        ("get_rooms", {}, ["sex", "drugs", "rock'n'roll"]),
        (
            "join",
            {"name": "test_client", "room": "lobby"},
            {"text": "welcome to lobby"},
        ),
    ],
    ids=idtype,
)
async def test_chat(conn: AsyncClient, event, data, expected):
    await conn.emit(event, data=data, namespace="/chat")
    await conn.sleep(2)
    assert expected in EXPECTED_CHAT_DATA


def riddle():
    riddle = Riddle()
    riddle.get_question()
    return riddle


@pytest.mark.parametrize(
    "event, data, expected",
    [
        ("connected", None, "connected"),
        ("next", {}, {"text": riddle().question}),
        (
            "answer",
            {"text": riddle().answer},
            {
                "riddle": riddle().question,
                "is_correct": "true",
                "answer": riddle().answer,
            },
        ),
        (
            "answer",
            {"text": "asd"},
            {
                "riddle": riddle().question,
                "is_correct": "false",
                "answer": riddle().answer,
            },
        ),
        ("score", {}, {"value": 1}),
        ("recreate", {}, {"text": riddle().question}),
    ],
    ids=idtype,
)
async def test_riddle(conn: AsyncClient, event, data, expected):
    await conn.emit(event, data=data, namespace="/riddle")
    await conn.sleep(2)
    assert expected in EXPECTED_RIDDLE_DATA


@pytest.mark.skip("Not implemented")
async def test_trivia(conn: AsyncClient, event, data, expected):
    pass
    # TODO: need to realise this functionality
