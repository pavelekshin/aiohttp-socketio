import logging
import logging.config

import socketio
from aiohttp import web
from aiohttp.web_app import Application

from src.apps.chat import Chat
from src.apps.riddle import Riddle
from src.apps.trivia import Trivia
from src.routes import setup_routes


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


async def context(app: Application):
    yield
    await app["sio"].shutdown()
