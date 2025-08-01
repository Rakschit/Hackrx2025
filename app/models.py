from pydantic import BaseModel, HttpUrl
from typing import List

class RunRequest(BaseModel):
    document: HttpUrl
    questions: List[str]
