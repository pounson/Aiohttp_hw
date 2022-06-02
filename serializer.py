import pydantic


class AdvertisementSerializer(pydantic.BaseModel):
    user: str
    title: str
    description: str

