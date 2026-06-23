from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    id: str
    temple_email: str
    display_name: str
    role: str
