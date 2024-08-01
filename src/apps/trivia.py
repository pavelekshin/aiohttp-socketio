import logging
from typing import Any

import socketio
from pydantic import ValidationError

from src.config.config_folder import get_config_folder
from src.helper import generate_game_uuid, send_status
from src.modules.mod import Client, ClientContainer, GameContainer, Trivia, WaitingRoom
from src.schemas.schema import TriviaOnAnswer, TriviaOnJoinGame, TriviaOnAnswerOut

client_container = ClientContainer()
game_container = GameContainer()
waiting_room = WaitingRoom()

logger = logging.getLogger("trivia")


class TriviaApp(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        await send_status(client_container, logger)

    async def on_get_topics(self, sid: str, data: dict[str, Any]):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        trivia = game_container.get_item("topics")
        topics_path = get_config_folder("trivia_topics.csv")
        trivia.load_topics(topics_path)
        topics = trivia.topics
        await self.emit("topics", to=sid, data=topics)

    async def on_join_game(self, sid: str, data: dict[str, Any]):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        try:
            user_msg = TriviaOnJoinGame(**data)
        except ValidationError as err:
            await self.emit("error", to=sid, data={"error": err.json()})
            logger.error(f"Client {sid} message validation error!")
        else:
            set_client_data(data=user_msg, sid=sid)
            waiting_room.add_sid_to_topic(user_msg.topic_pk, sid)
            if (
                    users_per_topic := waiting_room.get_sid_per_topic(user_msg.topic_pk)
            ) and len(users_per_topic) == 2:
                uid = generate_game_uuid()
                trivia = game_container.get_item(uid)
                for sid in users_per_topic:
                    trivia.add_user(sid)
                    client = client_container.get_item(sid)
                    client.game_uid = uid
                    await self.enter_room(sid, uid)
                waiting_room.clear_topic(user_msg.topic_pk)
                question_path = get_config_folder("trivia_questions.csv")
                trivia.load_questions(question_path)
                trivia.topic = user_msg.topic_pk
                body = create_answer_body(trivia=trivia, uid=uid)
                if trivia.remaining_question_on_topic(trivia.topic) > 0:
                    await self.emit("game", room=uid, data=body)
                    logger.info(
                        f'Send event "game" on {self.__class__.__qualname__} to {uid}, with body: {body}'
                    )
                else:
                    players = trivia.get_players()
                    body = {"players": players}
                    await self.emit("no_question", room=uid, data=body)
                    logger.info(
                        f'Send event "no_question" on {self.__class__.__qualname__} to {uid}, with body: {body}'
                    )
            else:
                await self.emit(None, data={})

    async def on_answer(self, sid: str, data: dict[str, Any]):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        client = client_container.get_item(sid)
        uid = client.game_uid
        try:
            msg = TriviaOnAnswer(**data)
        except ValidationError as err:
            await self.emit("error", to=sid, data={"error": err.json()})
            logger.error(f"Client {sid} message validation error!")
        else:
            trivia = game_container.get_item(uid)
            trivia.add_game_answer(msg.index, sid)
            if len(answers := trivia.get_game_answers()) > 1:
                check_answers(correct_answer=int(trivia.answer), answers=answers)
                if (trivia.remaining_question_on_topic(trivia.topic)) > 0:
                    body = create_answer_body(trivia=trivia, uid=uid)
                    await self.emit("game", room=uid, data=body)
                    logger.info(
                        f'Send event "game" on {self.__class__.__qualname__} to {uid}, with body: {body}'
                    )
                else:
                    players = trivia.get_players()
                    body = {"players": players}
                    await self.emit("over", room=uid, data=body)
                    logger.info(
                        f'Send event "over" on {self.__class__.__qualname__} to {uid}, with body: {body}'
                    )

    async def on_release_queue(self, sid: str, data: dict[str, Any]):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        waiting_room.remove_sid_from_waiting_room(sid)

    async def on_disconnect(self, sid: str):
        client = client_container.get_item(sid)
        logger.info(
            f"Client {sid} disconnected from {self.__class__.__qualname__},"
            f" connection time is : {client.connection_time()}"
        )
        run_clear_on_disconnect(client, sid)
        await send_status(client_container, logger)


def check_answers(*, correct_answer: int, answers: list[dict[str, Any]]):
    if not isinstance(answers, list):
        raise ValueError("Answers not provided!")
    elif correct_answer is None:
        raise AttributeError("Correct answer not provided!")
    for item in answers:
        if item.get("answer") == correct_answer:
            sid = item.get("sid")
            client = client_container.get_item(sid)
            game = client.game
            game.score_increment()


def create_answer_body(*, trivia: Trivia, uid: str):
    topic = trivia.topic
    if not topic:
        raise AttributeError("Topic for game not found!")
    count = trivia.remaining_question_on_topic(topic)
    trivia.get_question(topic)
    trivia.clear_game_answers()
    try:
        msg = TriviaOnAnswerOut(**{
            "uid": uid,
            "question_count": count,
            "players": trivia.get_players(),
            "answer": trivia.answer,
            "current_question": {
                "text": trivia.question,
                "options": trivia.options,
            },
        })
    except ValidationError as err:
        logger.error(f"Serialization error {err}")
    else:
        return msg.model_dump()


def run_clear_on_disconnect(client: Client, sid: str):
    waiting_room.remove_sid_from_waiting_room(sid)
    uid = client.game_uid
    game_container.del_item(uid)
    client_container.del_item(sid)
    del client
    del uid


def set_client_data(*, data: TriviaOnJoinGame, sid: str) -> None:
    if not data:
        raise AttributeError("The user data not provided!")
    if not sid:
        raise AttributeError("The user sid not provided!")
    client = client_container.get_item(sid)
    client.create_game("trivia")
    client.name = data.name
