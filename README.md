# SocketIO on Aiohttp

Hands-on experience with Socket.IO and Aiohttp.\
Project include three Socket.IO independent app: Chat, Riddle game and Multiplayer Trivia game.\
All three game glue together with custom classes.

- Aiohttp
- SocketIO
- pydantic
- logging
- pytest-asyncio
- mypy type checked
- custom class for business logic
- lightweight SocketIO js client
- site templates with Handlebars


well-structured code:

```bash
.
├── README.md
├── images
├── requremenets.txt
├── ruff.toml
├── src                                             -- src app
│   ├── helper.py
│   ├── main.py
│   ├── app.py
│   ├── routes.py                                   -- routes
│   ├── apps                                        -- apps
│   │   ├── chat.py
│   │   ├── riddle.py
│   │   └── trivia.py
│   ├── config
│   │   ├── config_folder.py
│   │   ├── logging.yaml
│   │   ├── trivia_questions.csv
│   │   └── trivia_topics.csv
│   ├── modules
│   │   └── mod.py                                  -- modules
│   ├── schemas                                     -- pydantic shema
│   │   └── schema.py
│   ├── static                            
│   │   ├── js
│   │   └── style
│   └── templates                                   -- site templates
└── tests                                           -- pytest
   ├── conftest.py
   ├── pytest.ini
   └── test_client.py

```

### Chat application:

![chat.png](images%2Fchat.png)

### Riddle application:

![riddle.png](images%2Friddle.png)

### Trivia application:

![trivia.png](images%2Ftrivia.png)
![trivia-2.png](images%2Ftrivia-2.png)