from pydantic import BaseModel, Field, field_serializer


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
