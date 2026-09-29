from pydantic import BaseModel
from uuid import UUID


class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    role: str


class TokenData(BaseModel):
    id:  UUID

    

    
    
    