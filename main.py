from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
import models, schemas
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from auth import create_access_token, get_current_user, verify_password, get_password_hash, \
    ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# test user that normally should be fetched from db etc
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "hashed_password": get_password_hash("testpassword"),
        "disabled": False,
    }
}


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/tracks/", response_model=List[schemas.Track])
async def read_tracks(name: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    query = select(
        models.Track.name,
        models.Album.title,
        models.Artist.name,
        models.Track.milliseconds,
        models.Genre.name,
    ).select_from(models.Track).join(models.Album, models.Track.album_id == models.Album.album_id).join(models.Artist, models.Album.artist_id == models.Artist.artist_id).join(models.Genre, models.Track.genre_id == models.Genre.genre_id)

    if name:
        query = query.where(models.Track.name.ilike(f"%{name}%"))

    result = await db.execute(query)
    tracks = result.all()


    print(current_user)

    return [
        schemas.Track(
            name=track.name,
            album=track.title,
            artist=track.name_1,
            duration=str(track.milliseconds // 1000),
            genre=track.name_2
        )
        for track in tracks
    ]