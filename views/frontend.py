from aiohttp import web


async def index(request):
    path = request.path
    return web.FileResponse(f"templates/{path}/index.html")
