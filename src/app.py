import logging
import logging.config

import socketio
from aiohttp import web
from aiohttp.web_app import Application

from src.apps.chat import ChatApp
from src.apps.riddle import RiddleApp
from src.apps.trivia import TriviaApp
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
    app["sio"].register_namespace(RiddleApp("/riddle"))
    app["sio"].register_namespace(ChatApp("/chat"))
    app["sio"].register_namespace(TriviaApp("/trivia"))

    # init app context
    app.cleanup_ctx.append(context)
    # init webapp routes
    setup_routes(app)
    return app


async def context(app: Application):
    yield
    await app["sio"].shutdown()
