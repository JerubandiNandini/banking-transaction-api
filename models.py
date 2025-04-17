from pydantic import BaseModel

class User(BaseModel):
    id: str
    username: str
    role: str
    account_id: str | None = None