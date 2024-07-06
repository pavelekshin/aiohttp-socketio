import logging
import logging.config

import socketio
import yaml
from aiohttp import web

from apps.chat import Chat
from apps.riddle import Riddle
from apps.trivia import Trivia
from routes import setup_routes


async def init_app():
    # Create webapp
    app = web.Application()
    # logger
    logging.basicConfig(level="DEBUG")
    logger = logging.getLogger()
    # init socketio.AsyncServer in app scope
    app["sio"] = socketio.AsyncServer(
        async_mode="aiohttp", logger=logger, engine_logger=logger
    )
    # Attach SocketIO to webapp
    app["sio"].attach(app)
    app["sio"].register_namespace(Riddle("/riddle"))
    app["sio"].register_namespace(Chat("/chat"))
    app["sio"].register_namespace(Trivia("/trivia"))

    # init app context
    app.cleanup_ctx.append(context)
    # init webapp routes
    setup_routes(app)
    return app


async def context(app):
    yield
    await app["sio"].shutdown()
