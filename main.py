import os
import asyncio
import telepot.aio
import random
from telepot.aio.loop import MessageLoop

from database import session, User, FirstChapter

loop = asyncio.get_event_loop()

async def on_message(message):
    """Called when a telegram message is received."""
    # If a private message is received, add the user to the database
    if message["chat"]["type"] == "private":
        # Search for the matching user in the database
        user = session.query(User).filter_by(id=message["chat"]["id"]).first()
        # If the user doesn't exist, create a new entry
        if user is None:
            user = User(message["from"]["id"], message["from"]["first_name"], message["from"].get("last_name"), message["from"].get("username"), message["from"].get("language_code"))
            # Add the user to the database
            session.add(user)
            session.commit()
            await user.message(nlessbot, "Welcome to Nameless!\nThere is no game here yet.\nOr maybe there is.")
            loop.create_task(call_every_x_seconds(advance_to_chapter_one, 10, user=user))
        # If the user is playing the prologue, answer appropriately
        if user.chapter == 0:
            if message["text"].lower() == "sas":
                await user.message(nlessbot, "sus")
            elif message["text"].lower() == "lol":
                await user.message(nlessbot, "haha")
            elif "wtf" in message["text"]:
                await user.message(nlessbot, "¯\_(ツ)_/¯")
        elif user.chapter == 1:
            data = session.query(FirstChapter).filter_by(user_id=user.id).first()
            if data.current_question == 0:
                data.game_topic = message["text"]
                data.current_question = 1
                session.commit()
                await user.message(nlessbot, "Hmmm. Interesting.")
                await asyncio.sleep(5)
                await user.message(nlessbot, "When do you think it will be released?")
            elif data.current_question == 1:
                if "half" in message["text"].lower() and "life" in message["text"].lower():
                    await user.message(nlessbot, "So... Never? I don't think so.")
                    return
                data.game_release = message["text"]
                data.current_question = 2
                session.commit()
                await user.message(nlessbot, "See you later then!")


async def call_every_x_seconds(coroutine: asyncio.coroutine, timeout: int, *args, **kwargs):
    """Call a function every x seconds, and stop calling it if it returns Ellipsis."""
    while True:
        # Await the coroutine
        result = await coroutine(*args, **kwargs)
        # Stop calling it if it returns ...
        if result is ...:
            break
        # Wait the time specified in timeout
        await asyncio.sleep(timeout)


async def advance_to_chapter_one(user):
    """Start chapter one. Maybe."""
    # Generate a random number from 0 to 99
    rolled_number = random.randrange(100)
    # 1% chance to pass the check, it should take around 16 minutes
    if rolled_number == 0:
        # Advance the chapter number
        user.chapter = 1
        # Create the row for this chapter's data
        data = FirstChapter(user)
        # Add the row to the database
        session.add(data)
        session.commit()
        # Introduce the chapter to the player
        await user.message(nlessbot, "What do you think this game will be about?")
        # Display that an user has advanced to a new chapter
        print(f"{user} has advanced to Chapter One!")
        # Stop calling the function
        return ...


# Get the bot token from envvars
nlessbot_token = os.environ["nameless_token"]
# Create the bot
nlessbot = telepot.aio.Bot(nlessbot_token)
# Initialize the event loop
loop.create_task(MessageLoop(nlessbot, {"chat": on_message}).run_forever())
# Add the events that were stopped when the script was taken down
users = session.query(User).all()
for user in users:
    if user.chapter == 0:
        loop.create_task(call_every_x_seconds(advance_to_chapter_one, 10, user=user))
# Run the event loop
try:
    loop.run_forever()
except KeyboardInterrupt:
    exit(0)