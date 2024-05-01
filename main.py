import asyncio
import logging

from aiohttp import web
from app import init_app


def run():
    app = init_app()
    logger = logging.getLogger()
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    web.run_app(app, port=8080, shutdown_timeout=3, access_log=logger, loop=loop)


if __name__ == '__main__':
    run()
