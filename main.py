import asyncio
import logging

from aiohttp import web
from app import init_app

if __name__ == '__main__':
    app = init_app()
    logger = logging.getLogger()
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    web.run_app(app, port=8080, shutdown_timeout=3, access_log=logger, loop=loop)
