from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Artist(Base):
    __tablename__ = "Artist"
    ArtistId = Column(Integer, primary_key=True, index=True)
    Name = Column(String)


class Album(Base):
    __tablename__ = "Album"
    AlbumId = Column(Integer, primary_key=True, index=True)
    Title = Column(String)
    ArtistId = Column(Integer, ForeignKey("Artist.ArtistId"))
    artist = relationship("Artist")


class Genre(Base):
    __tablename__ = "Genre"
    GenreId = Column(Integer, primary_key=True, index=True)
    Name = Column(String)


class Track(Base):
    __tablename__ = "Track"
    TrackId = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    AlbumId = Column(Integer, ForeignKey("Album.AlbumId"))
    GenreId = Column(Integer, ForeignKey("Genre.GenreId"))
    Milliseconds = Column(Integer)
    album = relationship("Album")
    genre = relationship("Genre")