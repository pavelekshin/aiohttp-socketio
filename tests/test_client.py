import asyncio

import pytest
import pytest_asyncio
import socketio
from aiohttp import web
from socketio import AsyncClient

from app import init_app
from apps.trivia import game_container, get_answer_body
from config.config_folder import get_config_folder
from helper import generate_game_uuid
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
    await conn.sleep(0.5)
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
            {"text": "WRONG"},
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
    await conn.sleep(0.5)
    assert expected in EXPECTED_RIDDLE_DATA


def trivia_topics():
    trivia = game_container.get_item("topics")
    topics_path = get_config_folder("trivia_topics.csv")
    trivia.load_topics(topics_path)
    topics = trivia.topics
    return topics


def trivia_game():
    topic = 5
    trivia = game_container.get_item("topics")
    question_path = get_config_folder("trivia_questions.csv")
    trivia.load_questions(question_path)
    trivia.topic = topic
    response = get_answer_body(trivia=trivia, topic=topic, uid=generate_game_uuid())
    EXPECTED_TRIVIA_DATA.append(response)
    return response


@pytest.mark.parametrize(
    "event, data, expected",
    [
        ("connected", None, "connected"),
        ("get_topics", {}, trivia_topics()),
        ("join_game", {"topic_pk": 5, "name": "Player_name"}, trivia_game()),
        # TODO: complete tests
    ],
    ids=idtype,
)
async def test_trivia(conn: AsyncClient, event, data, expected):
    await conn.emit(event, data=data, namespace="/trivia")
    await conn.sleep(0.5)
    assert expected in EXPECTED_TRIVIA_DATA
