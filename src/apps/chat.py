import logging

import socketio
from pydantic import ValidationError

from src.helper import send_status
from src.modules.mod import ClientContainer
from src.schemas.schema import OnChatJoin

client_container = ClientContainer()

logger = logging.getLogger("chat")
_ROOMS = ["sex", "drugs", "rock'n'roll"]


class ChatApp(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        client_container.get_item(sid)
        await send_status(client_container, logger)

    async def on_disconnect(self, sid):
        client = client_container.get_item(sid)
        client_container.del_item(sid)
        logger.info(
            f"Client: {sid} disconnected from {self.__class__.__qualname__}, "
            f"connection time is : {client.connection_time()}"
        )
        await send_status(client_container, logger)

    async def on_get_rooms(self, sid, data):
        await self.emit("rooms", to=sid, data=_ROOMS)

    async def on_join(self, sid, data):
        username = data.get("name")
        try:
            OnChatJoin(**data)
        except ValidationError as err:
            await self.emit("error", to=sid, data={"error": err.json()})
            logger.error(
                f"Client {sid} username validation error! Entered name: {username}"
            )
            raise ConnectionRefusedError("error", {"error": err.json()}) from err
        room = data.get("room")
        client = client_container.get_item(sid)
        client.name = username
        client.room = room
        await self.emit("move", to=sid, data={"room": room})
        await self.enter_room(sid, room)
        logger.info(f"Client {sid} with name: {username}, join the room: {room}")
        if len(messages := client.get_messages(room)):
            await self.emit("messages", to=sid, data=messages)
            logger.info(f"Client {sid} with name: {username}, load schemas: {messages}")
        await self.emit("message", to=sid, data={"text": f"welcome to {room}"})

    async def on_leave(self, sid, data):
        client = client_container.get_item(sid)
        room = client.room
        username = client.name
        await self.close_room(room=room)
        logger.info(f"Client {sid}, with name: {username} left the room: {room}")
        del client.room

    async def on_send_message(self, sid, data):
        client = client_container.get_item(sid)
        username = client.name
        room = client.room
        text = data.get("text")
        data = {"text": text, "author": username}
        await self.emit("message", data=data, room=room)
        logger.info(f"Client {sid} send message {data} on room: {room} ")
        client.add_message(room, data)
