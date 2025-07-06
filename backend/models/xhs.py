from pydantic import BaseModel


class UserData(BaseModel):
    gender: int
    images: str
    imageb: str
    guest: bool
    red_id: str
    user_id: str
    nickname: str
    desc: str


class UserResponse(BaseModel):
    code: int
    success: bool
    msg: str
    data: UserData 