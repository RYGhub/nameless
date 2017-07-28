from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db = create_engine("sqlite:///database.sqlite")

Base = declarative_base(bind=db)
Session = sessionmaker(bind=db)

# Using sqlite, only a single write session is available
session = Session()

class User(Base):
    """The basic data of a Telegram user"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    firstname = Column(String)
    lastname = Column(String)
    language = Column(String)
    chapter = Column(Integer)

    async def message(self, bot, text):
        await bot.sendMessage(self.id, text)

    def __init__(self, tid: int, firstname: str=None, lastname: str=None, username: str=None, language: str=None):
        self.id = tid
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.language = language
        self.chapter = 0

    def __repr__(self):
        return f"<User {self.id}>"

    def __str__(self):
        # Display the username
        if self.username is not None:
            return f"@{self.username}"
        # Display first name and last name
        if self.lastname is not None:
            return f"{self.firstname} {self.lastname}"
        # Fallback if no lastname
        return f"{self.firstname}"


class FirstChapter(Base):
    """The save data of the first chapter"""
    __tablename__ = "firstchapter"

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User")

    current_question = Column(Integer)
    game_topic = Column(String)
    game_release = Column(String)

    def __init__(self, user):
        self.user_id = user.id
        self.current_question = 0


class SecondChapter(Base):
    """The save data of the second chapter"""
    __tablename__ = "secondchapter"

    mic_user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    mic_user = relationship("User", foreign_keys=[mic_user_id])

    button_user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    button_user = relationship("User", foreign_keys=[button_user_id])

    target_button = Column(Integer, nullable=False)
    button_pressed = Column(Integer)

    def __init__(self, micuser, buttonuser, target):
        self.mic_user_id = micuser.id
        self.button_user_id = buttonuser.id
        self.target_button = target

# If the script is run as standalone, generate the database
if __name__ == "__main__":
    Base.metadata.create_all()