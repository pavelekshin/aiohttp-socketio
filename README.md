# SocketIO on Aiohttp

Hands-on experience with Socket.IO and Aiohttp.\
Project include three Socket.IO independent app: Chat, Riddle game and Multiplayer Trivia game.\
All three game glue together with custom classes.

- Aiohttp
- SocketIO
- pydantic
- logging
- pytest-asyncio
- custom class for business logic
- lightweight SocketIO js client
- site templates with Handlebars


well-structured code:

```bash
├── main.py 
├── app.py                                    - app factory
├── helper.py                                 - helper functions
├── routes.py                                 - routes
├── apps                                      - apps
│   ├── chat.py
│   ├── riddle.py
│   └── trivia.py
├── config                                    - config dir
│   ├── config_folder.py
│   ├── logging.yaml
│   ├── trivia_questions.csv
│   └── trivia_topics.csv
├── modules                                   - custom class 
│   └── modules.py
├── schemas                                   - pydantic schema
│   └── schema.py
├── static                                    - static site content
│   ├── js
│   └── style
├── templates                                 - site templates
│   ├── chat
│   ├── riddle
│   └── trivia
└── tests                                     - pytest
```

### Chat application:

![chat.png](images%2Fchat.png)

### Riddle application:

![riddle.png](images%2Friddle.png)

### Trivia application:

![trivia.png](images%2Ftrivia.png)
![trivia-2.png](images%2Ftrivia-2.png)