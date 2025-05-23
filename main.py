from contextlib import asynccontextmanager
from datetime import timedelta
from venv import logger
from strawberry.fastapi import GraphQLRouter
from graphql_schema import schema
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

from redis_client import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis_pool()
    yield
    await close_redis_pool()

app = FastAPI(lifespan=lifespan)

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


@app.get("/api/tracks", response_model=List[schemas.Track])
async def read_tracks(name: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    print("--- /api/tracks endpoint hit ---")
    query = select(
        models.Track.name.label("track_name"),
        models.Album.title.label("album_title"),
        models.Artist.name.label("artist_name"),
        models.Track.milliseconds.label("ms"),
        models.Genre.name.label("genre_name"),
    ).select_from(models.Track).join(models.Album, models.Track.album_id == models.Album.album_id).join(models.Artist, models.Album.artist_id == models.Artist.artist_id).join(models.Genre, models.Track.genre_id == models.Genre.genre_id)

    if name:
        query = query.where(models.Track.name.ilike(f"%{name}%"))

    result = await db.execute(query)
    tracks = result.all()


    logger.info(current_user)

    return [
        schemas.Track(
            name=track.track_name,
            album=track.album_title,
            artist=track.artist_name,
            duration=str(track.ms // 1000),
            genre=track.genre_name
        )
        for track in tracks
    ]



@app.get("/api/tracks-redis", response_model=List[schemas.Track])
async def read_tracks_redis(
        name: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    logger.info(current_user)
    cache_key = generate_cache_key("rest:tracks", name)
    cached_tracks = await get_cache(cache_key)

    if cached_tracks is not None:
        print(f"CACHE HIT for key: {cache_key}")
        return cached_tracks

    print(f"CACHE MISS for key: {cache_key}")

    query = select(
        models.Track.name.label("track_name"),
        models.Album.title.label("album_title"),
        models.Artist.name.label("artist_name"),
        models.Track.milliseconds.label("ms"),
        models.Genre.name.label("genre_name"),
    ).select_from(models.Track).join(models.Album, models.Track.album_id == models.Album.album_id).join(models.Artist, models.Album.artist_id == models.Artist.artist_id).join(models.Genre, models.Track.genre_id == models.Genre.genre_id)

    if name:
        query = query.where(models.Track.name.ilike(f"%{name}%"))

    result = await db.execute(query)
    db_tracks = result.all()

    response_cache = []

    for track in db_tracks:
        response_cache.append({
                "name":track.track_name,
                "album":track.album_title,
                "artist":track.artist_name,
                "duration":str(track.ms // 1000),
                "genre":track.genre_name
        }
        )

    # response_tracks = [
    #     schemas.Track(
    #         name=track.track_name,
    #         album=track.album_title,
    #         artist=track.artist_name,
    #         duration=str(track.ms // 1000),
    #         genre=track.genre_name
    #     )
    #
    # ]
    await set_cache(cache_key, response_cache)

    return response_cache


graphql_app = GraphQLRouter(schema)

app.include_router(
    graphql_app,
    prefix="/graphql",
    dependencies=[Depends(get_current_user)]
)


@app.post("/graphql", include_in_schema=False)
async def graphiql_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/graphql")
