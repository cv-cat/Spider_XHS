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

class Category(BaseModel):
    id: str
    name: str

class HomefeedCategoryResponse(BaseModel):
    categories: list[Category]
