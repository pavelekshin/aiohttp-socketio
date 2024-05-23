import csv
from collections import defaultdict
from datetime import datetime
from typing import Any, Generator
from weakref import WeakKeyDictionary


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

    def get_messages(self):
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

    def get_messages(self, room):
        if not room:
            raise AttributeError("The room doesn't pass!")
        return self._messages[room].get_messages()

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
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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

    _instances = WeakKeyDictionary()

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
    objects = None

    def get_item(self, item):
        """
        Get object from container by their SID or UID depends on subclass
        :param item: uid or game_id depends on child class
        :return: object of container
        """
        return self.objects[item]

    def del_item(self, item) -> None:
        """
        Delete object from container by their ID
        :param item:  uid or game_id depends on child class
        """
        if item in self.objects.keys():
            del self.objects[item]

    def __len__(self):
        return len(self.objects)

    def __repr__(self):
        return f"{type(self).__qualname__}(users={self.objects})"


class ClientContainer(Container):
    """
    Container, return information about Client by their SID
    """

    def __init__(self):
        self.objects = defaultdict(Client)


class GameContainer(Container):
    """
    Container, return information about Trivia instance by their UID
    """

    def __init__(self):
        self.objects = defaultdict(Trivia)


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
        return f"{type(self).__name__}(questions={self._questions},answer={self._answer},question={self._question},\
        score={self._score})"


class Riddle(Game):
    """
    Class store riddle game actions
    """

    _QUESTIONS = [
        ("Висит груша нельзя скушать?", "лампочка"),
        ("Зимой и летом одним цветом", "Ёлка"),
    ]

    def __init__(self):
        super().__init__()

    def get_question(self):
        if self._questions is None:
            self._questions = list(Riddle._QUESTIONS)
        try:
            self._question, self._answer = self._questions.pop()
        except IndexError:
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
        self._options = None
        self._users = []
        self._topic = None
        self._players_answers = []

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

    @staticmethod
    def load_topics(path) -> None:
        """
        Load Trivia topics from provided path
        :param path: topic file
        :return:
        """
        Trivia._topics = []
        for i in Trivia._read_csv(path):
            topic = i.get("pk")
            waiting_room = WaitingRoom()
            if waiting_room.get_sid_per_topic(topic):
                i["has_players"] = True
            Trivia._topics.append(i)

    def load_questions(self, path) -> None:
        """
        Load Trivia questions from provided path
        :param path: questions file
        """
        if self._questions is None:
            self._questions = defaultdict(list)
        for i in Trivia._read_csv(path):
            self._questions[i["topic"]].append(
                {
                    "text": i["text"],
                    "answer": i["answer"],
                    "options": [v for k, v in i.items() if k in ["1", "2", "3", "4"]],
                }
            )

    def _questions_per_topic(self, topic: str | int) -> list[dict]:
        """
        Provide question for topic
        :param topic: topic number
        :return: List with questions
        """
        t = str(topic)
        return self._questions.get(t)

    @property
    def topics(self) -> list[str]:
        return Trivia._topics

    @property
    def options(self) -> list[str]:
        return self._options

    @property
    def users(self) -> list[str]:
        return self._users

    def add_user(self, sid: str) -> None:
        if sid not in self.users:
            self._users.append(sid)

    @property
    def topic(self) -> str:
        return self._topic

    @topic.setter
    def topic(self, topic):
        t = str(topic)
        self._topic = t

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

    def get_question(self, topic: str | int) -> None:
        """
        Assign next question/answer/options per topic
        :param topic: topic number
        """
        try:
            current = self._questions_per_topic(topic).pop()
        except IndexError:
            self._answer = None
            self._options = None
            self._question = None
        else:
            indx = int(current.get("answer"))
            self._answer = indx
            self._options = current.get("options")
            self._question = current.get("text")

    def remaining_question_on_topic(self, topic) -> int:
        """
        Evaluate remaining question per topic
        :param topic: topic number
        :return: number of remaining question
        """
        t = str(topic)
        return len(self._questions.get(t))

    def add_game_answer(self, index, sid) -> None:
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
            del self._waiting_room[t]
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
        return f"{type(self).__qualname__}(waiting_room={self._waiting_room})"
