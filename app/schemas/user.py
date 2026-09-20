from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    name: str
    email: EmailStr
    image_url: str
    provider: str


class UserEnvelope(BaseModel):
    data: UserResponse
    message: str
