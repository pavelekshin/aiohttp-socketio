from aiohttp import web
from views import frontend


def setup_routes(app: web.Application):
    app.router.add_route("GET", "/riddle", frontend.index)
    app.router.add_route("GET", "/chat", frontend.index)
    app.router.add_route("GET", "/trivia", frontend.index)
    app.router.add_static("/static", "static")
