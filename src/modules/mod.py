import csv
from collections import defaultdict
from datetime import datetime
from numbers import Number
from typing import Any, Generator
from weakref import WeakKeyDictionary
from zoneinfo import ZoneInfo


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
            self._messages.append({"text": msg, "author": author})

    def get_messages(self) -> list[dict[str, Any]]:
        return self._messages

    def __repr__(self):
        return f"{type(self).__qualname__}(messages={self._messages})"


class Client:
    """
    Client class, store all information about single client
    """

    def __init__(self):
        self.game = None
        self.game_uid = None
        self.name = None
        self.room = None
        self._start = datetime.now()
        self._end = None
        self._messages = defaultdict(Messages)

    def get_messages(self, room: str):
        if not room:
            raise AttributeError("The room doesn't pass!")
        return self._messages[room].get_messages()

    def add_message(self, room: str, data: dict[str, Any]):
        if not room or not data:
            raise AttributeError("The required attribute doesn't pass!")
        self._messages[room].add_message(data)

    def connection_time(self):
        self._end = datetime.now()
        duration = self._end - self._start
        dt = datetime.fromtimestamp(duration.total_seconds(), tz=ZoneInfo("UTC"))
        return dt.strftime("%H:%M:%S")

    def create_game(self, name=None):
        if name is None:
            raise AttributeError("The name of game didn't pass at attribute!")
        match name.lower():
            case "riddle":
                self.game = Riddle()
            case "trivia":
                self.game = Trivia()
            case _:
                raise ValueError(f"The game {name}, not found!")

    def __repr__(self):
        return f"{type(self).__qualname__}(name={self.name}, room={self.room}\
            ,messages={self._messages}, start={self._start}, end={self._end}, game={self.game}, game_uid={self.game_uid})"


class SingletonsConstructor(type):
    """
    Singletons metaclass
    """

    _instances: WeakKeyDictionary = WeakKeyDictionary()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            instance = cls._instances[cls]
        return instance

    def __repr__(cls):
        return f"{type(cls).__qualname__}(_instances={cls._instances})"


class Container(metaclass=SingletonsConstructor):
    objects: defaultdict

    def __len__(self) -> int:
        return len(self.objects)

    def __repr__(self):
        return f"{type(self).__qualname__}(container={self.objects})"


class ClientContainer(Container):
    """
    Container, return information about Client by their SID
    """

    def __init__(self) -> None:
        self.objects = defaultdict(Client)

    def get_item(self, sid) -> Client:
        """
        Get client object from container by their SID
        :param sid: client SID
        :return: container
        """
        return self.objects[sid]

    def del_item(self, sid) -> None:
        """
        Delete client object from container by their SID
        :param sid: client SID
        """
        if sid in self.objects.keys():
            del self.objects[sid]


class GameContainer(Container):
    """
    Container, return information about Trivia instance by their UID
    """

    def __init__(self) -> None:
        self.objects = defaultdict(Trivia)

    def get_item(self, uid) -> "Trivia":
        """
        Get object from container by their UID
        :param uid: Game UID
        :return: Trivia container
        """
        return self.objects[uid]

    def del_item(self, uid) -> None:
        """
        Delete object from container by their UID
        :param uid: Game UID
        """
        if uid in self.objects.keys():
            del self.objects[uid]


class Game:
    """
    Class store game actions
    """

    def __init__(self) -> None:
        self._questions: Any = None
        self._question: Any = None
        self._answer: Any = None
        self._score = 0

    @property
    def question(self):
        return self._question

    @property
    def answer(self):
        return self._answer

    @property
    def score(self) -> int:
        return self._score

    def score_increment(self):
        self._score += 1

    def score_decrement(self):
        self._score -= 1

    def __repr__(self):
        return f"{type(self).__name__}(questions={self._questions},answer={self._answer},question={self._question},\
        score={self._score})"


class Riddle(Game):
    """
    Class store riddle game actions
    """

    _QUESTIONS: list[tuple[str, str]] = [
        ("Висит груша нельзя скушать?", "лампочка"),
        ("Зимой и летом одним цветом", "Ёлка"),
    ]

    def __init__(self):
        super().__init__()

    def get_question(self):
        if not self._questions:
            self._questions = list(Riddle._QUESTIONS)
        if self._questions:
            self._question, self._answer = self._questions.pop()
        else:
            self._answer = None
            self._question = None

    def recreate(self):
        self._questions += list(Riddle._QUESTIONS)


class Trivia(Game):
    """
    Class store trivia game actions
    """

    _topics: list[dict[str, Any]] = []

    def __init__(self) -> None:
        super().__init__()
        self._options: list[str] | None = None
        self._users: list = []
        self._topic: str | None = None
        self._players_answers: list[dict] = []

    @staticmethod
    def _read_csv(path) -> Generator[dict[str, Any], None, None]:
        """
        CSV reader
        :param path: path to file
        :return: Generator
        """
        with open(path, "r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                yield row

    @classmethod
    def load_topics(cls, path) -> None:
        """
        Load Trivia topics from provided path
        :param path: topic file
        :return:
        """
        cls._topics = []
        for i in Trivia._read_csv(path):
            topic = i.get("pk")
            waiting_room = WaitingRoom()
            if topic and waiting_room.get_sid_per_topic(str(topic)):
                i["has_players"] = True
            cls._topics.append(i)

    def load_questions(self, path) -> None:
        """
        Load Trivia questions from provided path
        :param path: questions file
        """
        if not self._questions:
            self._questions = defaultdict(list)
        for i in Trivia._read_csv(path):
            self._questions[i["topic"]].append(
                {
                    "text": i["text"],
                    "answer": i["answer"],
                    "options": [v for k, v in i.items() if k in ["1", "2", "3", "4"]],
                }
            )

    def _questions_per_topic(
        self, topic: str
    ) -> list[dict[str, int | str | list[str]]] | None:
        """
        Provide question for topics
        :param topic: topic number
        :return: List with questions
        """
        return self._questions.get(topic)

    @property
    def topics(self) -> list[dict[str, Any]]:
        return Trivia._topics

    @property
    def options(self) -> list[str] | None:
        return self._options

    @property
    def users(self) -> list[str]:
        return self._users

    def add_user(self, sid: str) -> None:
        if sid not in self.users:
            self._users.append(sid)

    @property
    def topic(self) -> str | None:
        return self._topic

    @topic.setter
    def topic(self, topic: str | Number):
        self._topic = str(topic)

    def get_players(self) -> list[dict]:
        """
        Get players with their scores
        :return: score for players
        """
        players = []
        if self.users:
            for sid in self._users:
                container = ClientContainer()
                client = container.get_item(sid)
                trivia = client.game
                players.append({"name": client.name, "score": trivia.score})
        return players

    def get_question(self, topic: str) -> None:
        """
        Assign next question/answer/options per topics
        :param topic: topic number
        """
        data = self._questions_per_topic(topic)
        if data:
            current = data.pop()
            indx = current.get("answer")
            self._answer = (
                int(indx) if isinstance(indx, int) or isinstance(indx, str) else None
            )
            self._options = current.get("options")
            self._question = current.get("text")
        else:
            self._answer = None
            self._options = None
            self._question = None

    def remaining_question_on_topic(self, topic: str | None) -> int:
        """
        Evaluate remaining question per topics
        :param topic: topic number
        :return: count of remaining question
        """
        if not topic:
            raise AttributeError("Topic not provided")
        elif self._questions and (q := self._questions.get(topic)):
            return len(q)
        return 0

    def add_game_answer(self, index: int, sid: str) -> None:
        """
        Add player answer
        :param index: number of player answer
        :param sid: player SID
        """
        answer_exist = False
        for answers in self._players_answers:
            if sid in answers.values():
                answer_exist = True
        if not answer_exist:
            self._players_answers.append({"answer": index, "sid": sid})

    def clear_game_answers(self) -> None:
        """
        Clear players answers, need clear after each question
        """
        self._players_answers.clear()

    def get_game_answers(self) -> list[dict]:
        """
        Get players answers
        :return:
        """
        return self._players_answers

    def __repr__(self):
        return (
            f"{super().__repr__()},topics={self._topics},options={self._options},users={self._users},"
            f"topic={self._topic},players_answers={self._players_answers}"
        )


class WaitingRoom(metaclass=SingletonsConstructor):
    """
    Class realise waiting room
    """

    def __init__(self) -> None:
        self._waiting_room: defaultdict[str, list[str]] = defaultdict(list)

    def add_sid_to_topic(self, topic: str, sid: str) -> None:
        """
        Add client SID to topic
        :param topic: topic_id
        :param sid: client sid
        :return:
        """
        if sid not in (topic_wr := self._waiting_room[topic]):
            topic_wr.append(sid)

    def remove_sid_from_topic(self, topic: str) -> None:
        """
        Remove client SID from topic
        :param topic: topic_id
        :return:
        """
        if topic in self._waiting_room.keys():
            if user_per_topic := self.get_sid_per_topic(topic):
                for sid in user_per_topic:
                    self._waiting_room[topic].remove(sid)
        else:
            raise ValueError("Topic not found!")

    def clear_topic(self, topic: str) -> None:
        """
        Clear topic
        :param topic: topic_id
        :return:
        """
        if topic in self._waiting_room.keys():
            del self._waiting_room[topic]
        else:
            raise ValueError("Topic not found!")

    def get_sid_per_topic(self, topic: str) -> list[str] | None:
        """
        Get users sid for topic
        :param topic: topic_id
        :return: return list of sid per topic
        """
        if not topic:
            raise AttributeError("Topic not provided!")
        return self._waiting_room.get(topic)

    def remove_sid_from_waiting_room(self, sid: str) -> None:
        """
        Remove user SID from waiting room
        :param sid: user SID
        :return:
        """
        for topic, sids in self._waiting_room.items():
            if (players := self._waiting_room.get(topic)) and sid in players:
                players.remove(sid)

    def __repr__(self):
        return f"{type(self).__qualname__}(waiting_room={self._waiting_room})"
