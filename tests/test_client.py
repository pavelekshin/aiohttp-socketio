import pytest
from socketio import AsyncClient

from src.apps.trivia import create_answer_body, game_container
from src.config.config_folder import get_config_folder
from src.helper import generate_game_uuid
from src.modules.mod import Riddle
from tests.conftest import (
    EXPECTED_CHAT_DATA,
    EXPECTED_RIDDLE_DATA,
    EXPECTED_TRIVIA_DATA,
    idtype,
)


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


def riddle_game():
    riddle = Riddle()
    riddle.get_question()
    return riddle


@pytest.mark.parametrize(
    "event, data, expected",
    [
        ("connected", None, "connected"),
        ("next", {}, {"text": riddle_game().question}),
        (
            "answer",
            {"text": riddle_game().answer},
            {
                "riddle": riddle_game().question,
                "is_correct": "true",
                "answer": riddle_game().answer,
            },
        ),
        (
            "answer",
            {"text": "WRONG"},
            {
                "riddle": riddle_game().question,
                "is_correct": "false",
                "answer": riddle_game().answer,
            },
        ),
        ("score", {}, {"value": 1}),
        ("recreate", {}, {"text": riddle_game().question}),
    ],
    ids=idtype,
)
async def test_riddle(conn: AsyncClient, event, data, expected):
    print(data)
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
    topic = "5"
    trivia = game_container.get_item("topics")
    question_path = get_config_folder("trivia_questions.csv")
    trivia.load_questions(question_path)
    trivia.topic = topic
    response = create_answer_body(trivia=trivia, uid=generate_game_uuid())
    EXPECTED_TRIVIA_DATA.append(response)
    return response


@pytest.mark.parametrize(
    "event, data, expected",
    [
        ("connected", None, "connected"),
        ("get_topics", {}, trivia_topics()),
        ("join_game", {"topic_pk": "5", "name": "Player_name"}, trivia_game()),
        # TODO: complete tests
    ],
    ids=idtype,
)
async def test_trivia(conn: AsyncClient, event, data, expected):
    await conn.emit(event, data=data, namespace="/trivia")
    await conn.sleep(0.5)
    assert expected in EXPECTED_TRIVIA_DATA
