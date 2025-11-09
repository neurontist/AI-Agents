from pydantic import BaseModel, Field
from typing import Literal, Optional

class MessageClassifier(BaseModel):
    message_type: Literal["database","mail","wikipedia"] = Field(
        description="Classify if the message related to operations on database, sending or " \
        "writing mail, or getting inforamation from wikipedia, " \
        "anything related to information on internet"
    )

class WikipediaClassifier(BaseModel):
    need_wikipedia: Literal["wikipedia_info","no_wikipedia_info"] = Field(
        description="Classify if the wikipedia tool is needed or not"
    )

class ExtractFields(BaseModel):
    column: str | None = Field(
        description="Your task is to extract search parameters from the user message. This is the name of the column to search for in database"
    )
    value: str | None = Field(
        description="Your task is to extract search parameters from the user message, name value can be misspelled by user or not fully written. Extract the value to search in the database"
    )

class MailExtraction(BaseModel):
    recipient_name: Optional[str]
    recipient_email: Optional[str]
    message_body: Optional[str]