import logging

import socketio
from pydantic import ValidationError

from modules.modules import ClientContainer
from schemas.schema import OnRiddleAnswer

client_container = ClientContainer()
logger = logging.getLogger("riddle")


class Riddle(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        client = client_container.get_user(sid)
        client.create_game("riddle")
        await self.send_status()

    async def on_disconnect(self, sid):
        client = client_container.get_user(sid)
        logger.info(f"Client {sid} connection time is : {client.connection_time()}")
        client_container.del_user(sid)
        logger.info(
            f"Client {sid} disconnected from {self.__class__.__qualname__}, remain clients count: {len(client_container)}")
        await self.send_status()

    async def on_next(self, sid, data):
        client = client_container.get_user(sid)
        riddle = client.get_game
        riddle.get_question()
        question = riddle.question
        if question is not None:
            await self.emit("riddle", to=sid, data={"text": question})
            logger.info(f"Send question: {question} to {sid}")
        else:
            await self.emit("over", to=sid, data={})
            logger.info(f"Send over to {sid}")

    async def on_recreate(self, sid, data):
        client = client_container.get_user(sid)
        riddle = client.get_game
        riddle.recreate()
        riddle.get_question()
        question = riddle.question
        await self.emit("riddle", to=sid, data={"text": question})
        logger.info(f"Send question: {question} to {sid}")

    async def on_answer(self, sid, data):
        logger.info(f"Client {sid} send data: {data}")
        text = str(data.get("text")).strip()
        client = client_container.get_user(sid)
        riddle = client.get_game
        answer = riddle.answer
        question = riddle.question
        if is_correct := text.lower() in answer.lower():
            riddle.score_increment()
        try:
            data = {"riddle": question, "is_correct": is_correct, "answer": answer}
            msg = OnRiddleAnswer(**data)
        except ValidationError as e:
            errors = e.json()
            await self.emit("errors", to=sid, data=errors)
            logger.error(f"Error occurred {errors}, sending to {sid}")
            return
        await self.emit("result", to=sid, data=msg.model_dump())
        logger.info(f"Send data {msg.model_dump_json()} to {sid}")
        await self.emit("score", to=sid, data={"value": riddle.score})

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
