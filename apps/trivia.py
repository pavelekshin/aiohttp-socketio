import logging
import uuid

import socketio

from config.config_folder import get_config_folder
from modules.modules import ClientContainer, WaitingRoom, GameContainer

client_container = ClientContainer()
game_container = GameContainer()
waiting_room = WaitingRoom()

logger = logging.getLogger("trivia")


class Trivia(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        await self.send_status()

    async def on_get_topics(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        trivia = game_container.get_game("topics")
        topics_path = get_config_folder("trivia_topics.csv")
        trivia.load_topics(topics_path)
        topics = trivia.topics
        await self.emit("topics", to=sid, data=topics)

    async def on_join_game(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        username = data.get("name")
        client = client_container.get_user(sid)
        client.create_game("trivia")
        client.name = username
        topic = data.get("topic_pk")
        waiting_room.add_sid_to_topic(topic, sid)
        if len(users_per_topic := waiting_room.get_sid_per_topic(topic)) == 2:
            uid = str(uuid.uuid4())
            trivia = game_container.get_game(uid)
            for sid in users_per_topic:
                trivia.add_user(sid)
                client = client_container.get_user(sid)
                client.game_uid = uid
                await self.enter_room(sid, uid)
            waiting_room.clear_topic(topic)
            question_path = get_config_folder("trivia_questions.csv")
            trivia.load_questions(question_path)
            trivia.topic = topic
            players = trivia.get_players()
            trivia.get_question(topic)
            count = trivia.remaining_question_on_topic(topic)
            payload = {"uid": uid,
                       "question_count": count,
                       "players": players,
                       "answer": trivia.answer,
                       "current_question": {"text": trivia.question,
                                            "options": trivia.options}
                       }
            await self.emit("game", room=uid, data=payload)
            logger.info(
                f"Send event \"game\" on {self.__class__.__qualname__} to {uid}, with body: {payload}")
        else:
            await self.emit(None, data={})

    async def on_answer(self, sid, data):
        logger.info(f"Client {sid} send data: {data} on {self.__class__.__qualname__}")
        client = client_container.get_user(sid)
        uid = client.game_uid
        player_answer = data.get("index")
        trivia = game_container.get_game(uid)
        trivia.add_game_answer(player_answer, sid)
        if len(answers := trivia.get_game_answers()) > 1:
            correct_answer = trivia.answer
            for item in answers:
                if item.get("answer") == correct_answer:
                    sid = item.get("sid")
                    client = client_container.get_user(sid)
                    game = client.get_game
                    game.score_increment()
            players = trivia.get_players()
            topic = trivia.topic
            if (count := trivia.remaining_question_on_topic(topic)) > 0:
                trivia.get_question(topic)
                trivia.clear_game_answers()
                payload = {"uid": uid,
                           "question_count": count,
                           "players": players,
                           "answer": trivia.answer,
                           "current_question": {"text": trivia.question,
                                                "options": trivia.options}}

                await self.emit("game", room=uid, data=payload)
                logger.info(
                    f"Send event \"game\" on {self.__class__.__qualname__} to {uid}, with body: {payload}")

            else:
                await self.emit("over", room=uid, data={"players": players})
                logger.info(
                    f"Send event \"over\" on {self.__class__.__qualname__} to {uid}, with body: {players}")
        else:
            # do nothing if we receive only one answer
            pass

    async def on_disconnect(self, sid):
        client = client_container.get_user(sid)
        logger.info(f"Client {sid} connection time is : {client.connection_time()}")
        waiting_room.remove_sid_from_waiting_room(sid)
        uid = client.game_uid
        game_container.del_game(uid)
        logger.info(
            f"Client: {sid} disconnected from {self.__class__.__qualname__}, remain clients count: {len(client_container)}")
        await self.send_status()

    @staticmethod
    async def send_status():
        match len(client_container):
            case 0:
                status = "Server is empty"
            case 1:
                status = "Server has one client"
            case 2 | 3:
                status = "Server has 2 or 3 clients"
            case _:
                status = "Server has 3 more clients"
        logger.info(status)
