from typing import Annotated

from pydantic import (
    UUID4,
    BaseModel,
    Field,
    PlainSerializer,
    PlainValidator,
)


class ChatOnJoin(BaseModel):
    """
    Validation "join" event chat messages
    """

    name: str = Field(min_length=3, max_length=15)
    room: str = Field(str)


class RiddleOnAnswerOut(BaseModel):
    """
    Serializer for "answer" event riddle messages
    """

    riddle: str = Field(str)
    is_correct: Annotated[
        bool, PlainSerializer(lambda item: str(item).lower(), return_type=str)
    ]
    answer: str = Field(str)


class TriviaOnJoinGame(BaseModel):
    topic_pk: Annotated[
        str,
        PlainValidator(lambda item: str(item)),
    ]
    name: Annotated[str, Field(min_length=3)]


class TriviaOnAnswer(BaseModel):
    index: int = Field(ge=0)
    game_uid: UUID4


class TriviaCurrentQuestion(BaseModel):
    text: str
    options: list[str]


class TriviaOnAnswerOut(BaseModel):
    uid: UUID4
    question_count: int
    players: list[dict]
    answer: int
    current_question: TriviaCurrentQuestion
