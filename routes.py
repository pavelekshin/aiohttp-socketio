from aiohttp import web


async def index(request):
    path = request.path
    return web.FileResponse(f"templates/{path}/index.html")


def setup_routes(app: web.Application):
    app.router.add_route("GET", "/riddle", index)
    app.router.add_route("GET", "/chat", index)
    app.router.add_route("GET", "/trivia", index)
    app.router.add_static("/static", "static")
