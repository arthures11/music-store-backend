import strawberry
from typing import List, Optional
import models
from database import get_db
from sqlalchemy.future import select
from sqlalchemy import func

@strawberry.type
class TrackType:
    name: str
    album: str
    artist: str
    duration: str
    genre: str


async def get_tracks_resolver(name_filter: Optional[str] = None) -> List[TrackType]:
    async for db in get_db():
        query = select(
            models.Track.name.label("name"),
            models.Album.title.label("album"),
            models.Artist.name.label("artist"),
            models.Track.milliseconds.label("duration_ms"),
            models.Genre.name.label("genre")
        ).select_from(models.Track).join(
            models.Album, models.Track.album_id == models.Album.album_id
        ).join(
            models.Artist, models.Album.artist_id == models.Artist.artist_id
        ).join(
            models.Genre, models.Track.genre_id == models.Genre.genre_id
        )

        if name_filter:
            query = query.where(func.lower(models.Track.name).like(f"%{name_filter.lower()}%"))

        result = await db.execute(query)
        tracks_data = result.all()

        tracks_list = []
        for track in tracks_data:
            duration_seconds = str(track.duration_ms // 1000) if track.duration_ms else "0"
            tracks_list.append(
                TrackType(
                    name=track.name,
                    album=track.album,
                    artist=track.artist,
                    duration=duration_seconds,
                    genre=track.genre
                )
            )
        return tracks_list


@strawberry.type
class Query:
    @strawberry.field
    async def tracks(self, nameFilter: Optional[str] = None) -> List[TrackType]:
        """fetchin tracks with optional name filtering"""
        return await get_tracks_resolver(name_filter=nameFilter)

schema = strawberry.Schema(query=Query)