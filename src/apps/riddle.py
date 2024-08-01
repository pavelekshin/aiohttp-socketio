import logging
from typing import Any

import socketio
from pydantic import ValidationError

from src.helper import send_status
from src.modules.mod import ClientContainer, Client
from src.schemas.schema import RiddleOnAnswerOut

client_container = ClientContainer()
logger = logging.getLogger("riddle")


class RiddleApp(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        client = client_container.get_item(sid)
        client.create_game("riddle")
        await send_status(client_container, logger)

    async def on_disconnect(self, sid: str):
        client = client_container.get_item(sid)
        client_container.del_item(sid)
        logger.info(
            f"Client {sid} disconnected from {self.__class__.__qualname__},"
            f" connection time is : {client.connection_time()}"
        )
        await send_status(client_container, logger)

    async def on_next(self, sid: str, data: dict[str, Any]):
        client = client_container.get_item(sid)
        riddle = client.game
        riddle.get_question()
        question = riddle.question
        if question is not None:
            await self.emit("riddle", to=sid, data={"text": question})
            logger.info(f"Send question: {question} to {sid}")
        else:
            await self.emit("over", to=sid, data={})
            logger.info(f"Send over to {sid}")

    async def on_answer(self, sid: str, data: dict[str, Any]):
        logger.info(f"Client {sid} send data: {data}")
        text = str(data.get("text")).strip()
        client = client_container.get_item(sid)
        riddle = client.game
        answer = riddle.answer
        question = riddle.question
        if (is_correct := text.lower()) == answer.lower():
            riddle.score_increment()
        try:
            msg = RiddleOnAnswerOut(
                **{
                    "riddle": question,
                    "is_correct": is_correct,
                    "answer": answer,
                }
            )
        except ValidationError as err:
            await self.emit("errors", to=sid, data=err.json())
            logger.error(f"Error occurred {err.json()}, sending to {sid}")
        else:
            await self.emit("result", to=sid, data=msg.model_dump())
            logger.info(f"Send data {msg.model_dump()} to {sid}")
            await self.emit("score", to=sid, data={"value": riddle.score})

    async def on_recreate(self, sid: str, data: dict[str, Any]):
        client = client_container.get_item(sid)
        riddle = client.game
        riddle.recreate()
        await self.emit("riddle", to=sid, data={"text": riddle.get_question()})
        logger.info(f"Send question: {riddle.get_question()} to {sid}")
