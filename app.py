import logging
import logging.config
import socketio
import yaml
from aiohttp import web
from apps.chat import Chat
from apps.riddle import Riddle
from apps.trivia import Trivia
from config.config_folder import get_config_folder
from routes.routes import setup_routes


async def init_app():
    # Create webapp
    app = web.Application()
    # logger
    logger_path = get_config_folder("logging.yaml")
    init_logger(logger_path)
    logger = logging.getLogger()
    # init socketio.AsyncServer in app scope
    app["sio"] = socketio.AsyncServer(async_mode="aiohttp", logger=logger, engine_logger=logger)
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


def init_logger(config_path):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file.read())
    logging.config.dictConfig(config)
