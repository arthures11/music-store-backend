# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
import models, schemas
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_

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

@app.get("/api/tracks/", response_model=List[schemas.Track])
async def read_tracks(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    retrieves tracks from the database, optionally filtering by name.
    """
    query = select(
        models.Track.Name,
        models.Album.Title,
        models.Artist.Name,
        models.Track.Milliseconds,
        models.Genre.Name
    ).select_from(models.Track).join(models.Album, models.Track.AlbumId == models.Album.AlbumId).join(models.Artist, models.Album.ArtistId == models.Artist.ArtistId).join(models.Genre, models.Track.GenreId == models.Genre.GenreId)

    if name:
        query = query.where(models.Track.Name.ilike(f"%{name}%"))  # case-insensitive search

    result = await db.execute(query)
    tracks = result.all()

    return [
        schemas.Track(
            name=track.Name,
            album=track.Title,
            artist=track.Name_1,
            duration=str(track.Milliseconds // 1000),  # converting duration to be outputted as seconds
            genre=track.Name_2
        )
        for track in tracks
    ]