from typing import Annotated

from pydantic import (
    UUID4,
    BaseModel,
    Field,
    PlainValidator,
    field_serializer,
)


class OnChatJoin(BaseModel):
    """
    Validation "join" event chat messages
    """

    name: str = Field(min_length=3, max_length=15)
    room: str = Field(str)


class OnRiddleAnswer(BaseModel):
    """
    Serializer for "answer" event riddle messages
    """

    riddle: str = Field(str)
    is_correct: bool
    answer: str = Field(str)

    @field_serializer("is_correct", return_type=str)
    def serialize_bool(self, is_correct: bool) -> str:
        return str(is_correct).lower()


class TriviaOnJoinGame(BaseModel):
    topic_pk: Annotated[
        str,
        Field(ge=0),
        PlainValidator(lambda item: str(item)),
    ]
    name: Annotated[str, Field(min_length=3)]


class TriviaOnAnswer(BaseModel):
    index: int = Field(ge=0)
    game_uid: UUID4
