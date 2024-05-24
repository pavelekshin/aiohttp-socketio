import uuid


async def send_status(client_container, logger):
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


def generate_game_uuid():
    return str(uuid.uuid4())
