import asyncio
import logging

from aiohttp import web

from app import init_app


def run():
    app = init_app()
    logger = logging.getLogger()
    web.run_app(app, port=8080, shutdown_timeout=3)


if __name__ == "__main__":
    run()
