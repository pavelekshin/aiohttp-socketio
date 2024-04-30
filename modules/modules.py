from collections import defaultdict
from copy import deepcopy
from datetime import datetime
import csv
from typing import Generator, Any, Sequence, MutableSequence


class Messages:
    """
    Class store author messages
    """

    def __init__(self):
        self._messages = []

    def add_message(self, message):
        msg = message.get("text")
        author = message.get("author")
        if len(msg.strip()) > 0:
            self._messages.append(
                {
                    "text": msg,
                    "author": author
                })

    @property
    def get_messages(self):
        return self._messages

    def __repr__(self):
        return f"{type(self).__qualname__}(messages={self._messages})"


class Client:
    """
    Client class, store all information about single client
    """

    def __init__(self):
        self._name = None
        self._room = None
        self._start = datetime.now()
        self._end = None
        self._game = None
        self._messages = defaultdict(Messages)
        self._game_uid = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, room):
        self._room = room

    @room.deleter
    def room(self):
        self._room = None

    @property
    def game_uid(self):
        return self._game_uid

    @game_uid.setter
    def game_uid(self, value):
        self._game_uid = value

    @game_uid.deleter
    def game_uid(self):
        self._game_uid = None

    def get_messages(self, room):
        if not room:
            raise AttributeError("The room doesn't pass!")
        return self._messages[room].get_messages

    def add_message(self, room, data):
        if not room or not data:
            raise AttributeError("The required attribute doesn't pass!")
        self._messages[room].add_message(data)

    def connection_time(self):
        self._end = datetime.now()
        duration = self._end - self._start
        seconds = duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def create_game(self, name=None):
        if name is None:
            raise AttributeError("The name of game didn't pass at attribute!")
        elif name:
            match name.lower():
                case "riddle":
                    self._game = Riddle()
                case "trivia":
                    self._game = Trivia()
                case _:
                    raise ValueError(f"The game {name}, not found!")
        else:
            raise ValueError(f"Cannot create game {name}")

    @property
    def get_game(self):
        return self._game

    def __repr__(self):
        return f"{type(self).__qualname__}(name={self._name}, room={self._room}\
        ,messages={self._messages}, start={self._start}, end={self._end}, game={self._game}, game_uid={self._game_uid})"


class SingletonsConstructor(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            instance = cls._instances[cls]
        return instance

    def __repr__(self):
        return f"{type(self).__qualname__}(_instances={self._instances})"


class ClientContainer(metaclass=SingletonsConstructor):
    """
    Container, return information about Client by their SID
    """

    def __init__(self):
        self._users = defaultdict(Client)

    def get_user(self, sid):
        return self._users[sid]

    def del_user(self, sid):
        del self._users[sid]

    def __len__(self):
        return len(self._users)

    def __repr__(self):
        return f"{type(self).__qualname__}(users={self._users})"


class GameContainer(metaclass=SingletonsConstructor):
    """
    Container, return information about Trivia instance by their UID
    """

    def __init__(self):
        self._games = defaultdict(Trivia)

    def get_game(self, uid):
        return self._games[uid]

    def del_game(self, uid):
        del self._games[uid]

    def __len__(self):
        return len(self._games)

    def __repr__(self):
        return f"{type(self).__qualname__}(games={self._games})"


class Game:
    """
    Class store game actions
    """

    def __init__(self):
        self._questions = None
        self._question = None
        self._answer = None
        self._score = 0

    @property
    def question(self):
        return self._question

    @property
    def answer(self):
        return self._answer

    @property
    def score(self):
        return self._score

    def score_increment(self):
        self._score += 1

    def score_decrement(self):
        self._score -= 1

    def __repr__(self):
        return f"{type(self).__qualname__}(questions={self._questions},answer={self._answer},question={self._question},\
        score={self._score})"


class Riddle(Game):
    """
    Class store riddle game actions
    """

    _QUESTIONS = [
        ("Висит груша нельзя скушать?", "лампочка"), ("Зимой и летом одним цветом", "Ёлка")
    ]

    def get_question(self):
        if self._questions is None:
            self._questions = list(Riddle._QUESTIONS)
        if len(self._questions) > 0:
            self._question, self._answer = self._questions.pop()
        else:
            self._answer = None
            self._question = None

    def recreate(self):
        self._questions += list(Riddle._QUESTIONS)


class Trivia(Game):
    _topics = []

    """
    Class store trivia game actions
    """

    def __init__(self):
        super().__init__()
        self._topics = []
        self._options = None
        self._users = []
        self._topic = None
        self._players_answers = []

    @staticmethod
    def _read_csv(path) -> Generator[Any, None, None]:
        with open(path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                yield row

    @staticmethod
    def load_topics(path):
        Trivia._topics = []
        for i in Trivia._read_csv(path):
            topic = i.get("pk")
            waiting_room = WaitingRoom()
            if waiting_room.get_sid_per_topic(topic):
                i["has_players"] = True
            Trivia._topics.append(i)

    def load_questions(self, path):
        if self._questions is None:
            self._questions = defaultdict(list)
        for i in Trivia._read_csv(path):
            self._questions[i["topic"]].append({
                "text": i["text"],
                "answer": i["answer"],
                "options": [v for k, v in i.items() if k in ["1", "2", "3", "4"]]
            })

    @property
    def topics(self):
        return Trivia._topics

    def _questions_per_topic(self, topic: str | int):
        t = str(topic)
        return self._questions.get(t)

    @property
    def options(self):
        return self._options

    @property
    def users(self):
        return self._users

    def add_user(self, sid: str):
        if sid not in self.users:
            self._users.append(sid)

    @property
    def topic(self):
        return self._topic

    @topic.setter
    def topic(self, topic):
        t = str(topic)
        self._topic = t

    def get_players(self):
        players = []
        if users := self.users:
            for sid in users:
                container = ClientContainer()
                client = container.get_user(sid)
                trivia = client.get_game
                players.append({
                    "name": client.name,
                    "score": trivia.score
                })
        return players

    def get_question(self, topic: str | int):
        if len(self._questions_per_topic(topic)) > 0:
            current = self._questions_per_topic(topic).pop()
            indx = int(current.get("answer"))
            self._answer = indx
            self._options = current.get("options")
            self._question = current.get("text")
        else:
            self._answer = None
            self._options = None
            self._question = None

    def remaining_question_on_topic(self, topic):
        t = str(topic)
        return len(self._questions.get(t))

    def add_game_answer(self, index, sid):
        flag = False
        for answers in self._players_answers:
            if sid in answers.values():
                flag = True
        if not flag:
            self._players_answers.append({
                "answer": index,
                "sid": sid
            })
        print(self._players_answers)

    def clear_game_answers(self):
        self._players_answers.clear()

    def get_game_answers(self):
        return self._players_answers

    def __repr__(self):
        return (f"{super().__repr__()},topics={self._topics},options={self._options},user={self._users},"
                f"topic={self._topic},players_answers={self._players_answers}")


class WaitingRoom(metaclass=SingletonsConstructor):
    """
    Class realise waiting room
    """

    def __init__(self):
        self._waiting_room = defaultdict(list)

    def add_sid_to_topic(self, topic, sid):
        t = str(topic)
        if sid not in (topic := self._waiting_room[t]):
            topic.append(sid)

    def remove_sid_from_topic(self, topic):
        t = str(topic)
        if t in self._waiting_room.keys():
            user_per_topic = self.get_sid_per_topic(topic)
            for sid in user_per_topic:
                self._waiting_room[t].remove(sid)
        else:
            raise ValueError("Topic not found!")

    def clear_topic(self, topic):
        t = str(topic)
        if t in self._waiting_room.keys():
            self._waiting_room[t].clear()
        else:
            raise ValueError("Topic not found!")

    def get_sid_per_topic(self, topic):
        t = str(topic)
        return self._waiting_room.get(t)

    def remove_sid_from_waiting_room(self, sid):
        for topic, sids in self._waiting_room.items():
            if sid in (players := self._waiting_room.get(topic)):
                players.remove(sid)

    def __repr__(self):
        return f"{type(self).__qualname__},waiting_room={self._waiting_room}"
