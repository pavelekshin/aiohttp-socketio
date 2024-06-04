import logging

import socketio

from config.config_folder import get_config_folder
from helper import generate_game_uuid, send_status
from modules.modules import ClientContainer, GameContainer, WaitingRoom

client_container = ClientContainer()
game_container = GameContainer()
waiting_room = WaitingRoom()

logger = logging.getLogger("trivia")


class Trivia(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        await send_status(client_container, logger)

    async def on_get_topics(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        trivia = game_container.get_item("topics")
        topics_path = get_config_folder("trivia_topics.csv")
        trivia.load_topics(topics_path)
        topics = trivia.topics
        await self.emit("topics", to=sid, data=topics)

    async def on_join_game(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        topic = set_client_data_and_get_topic(data=data, sid=sid)
        waiting_room.add_sid_to_topic(topic, sid)
        if len(users_per_topic := waiting_room.get_sid_per_topic(topic)) == 2:
            uid = generate_game_uuid()
            trivia = game_container.get_item(uid)
            for sid in users_per_topic:
                trivia.add_user(sid)
                client = client_container.get_item(sid)
                client.game_uid = uid
                await self.enter_room(sid, uid)
            waiting_room.clear_topic(topic)
            question_path = get_config_folder("trivia_questions.csv")
            trivia.load_questions(question_path)
            trivia.topic = topic
            body = get_answer_body(trivia=trivia, topic=topic, uid=uid)
            await self.emit("game", room=uid, data=body)
            logger.info(
                f'Send event "game" on {self.__class__.__qualname__} to {uid}, with body: {body}'
            )
        else:
            await self.emit(None, data={})

    async def on_answer(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        client = client_container.get_item(sid)
        uid = client.game_uid
        player_answer = data.get("index")
        trivia = game_container.get_item(uid)
        trivia.add_game_answer(player_answer, sid)
        if len(answers := trivia.get_game_answers()) > 1:
            check_answers(correct_answer=trivia.answer, answers=answers)
            if (trivia.remaining_question_on_topic(trivia.topic)) > 0:
                body = get_answer_body(trivia=trivia, topic=trivia.topic, uid=uid)
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
        else:  # do nothing if we receive only one answer
            pass

    async def on_release_queue(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        waiting_room.remove_sid_from_waiting_room(sid)

    async def on_disconnect(self, sid):
        client = client_container.get_item(sid)
        logger.info(
            f"Client {sid} disconnected from {self.__class__.__qualname__},"
            f" connection time is : {client.connection_time()}"
        )
        run_clear_on_disconnect(client, sid)
        await send_status(client_container, logger)


def check_answers(*, correct_answer=None, answers=None):
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


def get_answer_body(*, trivia=None, topic=None, uid=None):
    players = trivia.get_players()
    count = trivia.remaining_question_on_topic(topic)
    trivia.get_question(topic)
    trivia.clear_game_answers()
    return {
        "uid": uid,
        "question_count": count,
        "players": players,
        "answer": trivia.answer,
        "current_question": {"text": trivia.question, "options": trivia.options},
    }


def run_clear_on_disconnect(client, sid):
    waiting_room.remove_sid_from_waiting_room(sid)
    uid = client.game_uid
    game_container.del_item(uid)
    client_container.del_item(sid)
    del client
    del uid


def set_client_data_and_get_topic(*, data=None, sid=None):
    if not isinstance(data, dict):
        raise ValueError("Data not provided!")
    elif not sid:
        raise AttributeError("The user sid not provided!")
    username = data.get("name")
    client = client_container.get_item(sid)
    client.create_game("trivia")
    client.name = username
    topic = data.get("topic_pk")
    return topic
