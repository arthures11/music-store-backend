from pydantic import BaseModel

class TrackBase(BaseModel):
    name: str
    album: str
    artist: str
    duration: str
    genre: str

class Track(TrackBase):
    class Config:
        from_attributes = True