from pydantic import BaseModel

class LoginRequest(BaseModel):
    identifier: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: dict
