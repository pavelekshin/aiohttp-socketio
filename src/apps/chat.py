import logging
from typing import Any

import socketio
from pydantic import ValidationError

from src.helper import send_status
from src.modules.mod import ClientContainer
from src.schemas.schema import OnChatJoin

client_container = ClientContainer()

logger = logging.getLogger("chat")
_ROOMS = ["sex", "drugs", "rock'n'roll"]


class ChatApp(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        client_container.get_item(sid)
        await send_status(client_container, logger)

    async def on_disconnect(self, sid: str):
        client = client_container.get_item(sid)
        client_container.del_item(sid)
        logger.info(
            f"Client: {sid} disconnected from {self.__class__.__qualname__}, "
            f"connection time is : {client.connection_time()}"
        )
        await send_status(client_container, logger)

    async def on_get_rooms(self, sid: str, data: dict[str, Any]):
        await self.emit("rooms", to=sid, data=_ROOMS)

    async def on_join(self, sid: str, data: dict[str, Any]):
        try:
            msg = OnChatJoin(**data)
        except ValidationError as err:
            await self.emit("error", to=sid, data={"error": err.json()})
            logger.error(f"Client {sid} validation error! Error: {err.json()}")
            raise ConnectionRefusedError("error", {"error": err.json()}) from err
        else:
            client = client_container.get_item(sid)
            client.name = msg.name
            client.room = msg.room
            await self.emit("move", to=sid, data={"room": msg.room})
            await self.enter_room(sid, msg.room)
            logger.info(
                f"Client {sid} with name: {msg.name}, join the room: {msg.room}"
            )
            if len(messages := client.get_messages(msg.room)):
                await self.emit("messages", to=sid, data=messages)
                logger.info(
                    f"Client {sid} with name: {msg.name}, load schemas: {messages}"
                )
            await self.emit("message", to=sid, data={"text": f"welcome to {msg.room}"})

    async def on_leave(self, sid: str, data: dict[str, Any]):
        client = client_container.get_item(sid)
        room = client.room
        username = client.name
        await self.close_room(room=room)
        logger.info(f"Client {sid}, with name: {username} left the room: {room}")
        del client.room

    async def on_send_message(self, sid: str, data: dict[str, Any]):
        client = client_container.get_item(sid)
        username = client.name
        room = client.room
        text = data.get("text")
        await self.emit("message", data={"text": text, "author": username}, room=room)
        logger.info(f"Client {sid} send message {data} on room: {room} ")
        client.add_message(room, data)
