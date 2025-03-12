from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Artist(Base):
    __tablename__ = "Artist"
    artist_id = Column("ArtistId", Integer, primary_key=True, index=True)
    name = Column(String)

class Album(Base):
    __tablename__ = "Album"
    album_id = Column("AlbumId", Integer, primary_key=True, index=True)
    title = Column(String)
    artist_id = Column("ArtistId", ForeignKey("Artist.ArtistId"))
    artist = relationship("Artist")

class Genre(Base):
    __tablename__ = "Genre"
    genre_id = Column("GenreId", primary_key=True, index=True)
    name = Column(String)

class Track(Base):
    __tablename__ = "Track"
    track_id = Column("TrackId", Integer, primary_key=True, index=True)
    name = Column(String)
    album_id = Column("AlbumId", Integer, ForeignKey("Album.AlbumId"))
    genre_id = Column("GenreId", ForeignKey("Genre.GenreId"))
    milliseconds = Column(Integer)
    album = relationship("Album")
    genre = relationship("Genre")