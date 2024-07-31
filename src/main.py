from aiohttp import web

from src.app import init_app


def run():
    app = init_app()
    web.run_app(app, port=8080, shutdown_timeout=3)


if __name__ == "__main__":
    run()
