import socketio
import logging

from pydantic import ValidationError

from modules.modules import ClientContainer
from schemas.schema import OnChatJoin

client_container = ClientContainer()

logger = logging.getLogger("chat")
_ROOMS = ["lobby", "general", "random"]


class Chat(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        logger.info(f"Client {sid} connect to {self.__class__.__qualname__}")
        client_container.get_item(sid)
        await self.send_status()

    async def on_disconnect(self, sid):
        client = client_container.get_item(sid)
        logger.info(f"Client {sid} connection time is : {client.connection_time()}")
        client_container.del_item(sid)
        logger.info(
            f"Client: {sid} disconnected from {self.__class__.__qualname__}, remain clients count: {len(client_container)}")
        await self.send_status()

    async def on_get_rooms(self, sid, data):
        await self.emit("rooms", to=sid, data=_ROOMS)

    async def on_join(self, sid, data):
        username = data.get("name")
        try:
            OnChatJoin(**data)
        except ValidationError as e:
            await self.emit("error", to=sid, data={"error": e.json()})
            logger.error(f"Client {sid} username validation error! Entered name: {username}")
            raise ConnectionRefusedError("error", {"error": e.json()})
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
