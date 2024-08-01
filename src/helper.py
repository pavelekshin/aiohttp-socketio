import uuid
from logging import Logger

from src.modules.mod import ClientContainer


async def send_status(client_container: ClientContainer, logger: Logger):
    match len(client_container):
        case 0:
            status = "Server is empty"
        case 1:
            status = "Server has one client"
        case 2 | 3:
            status = "Server has 2 or 3 clients"
        case _:
            status = "Server has 3 more clients"
    logger.info(status)


def generate_game_uuid() -> str:
    return str(uuid.uuid4())
