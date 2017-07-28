import os
import asyncio
import telepot.aio
import random
from telepot.aio.loop import MessageLoop
from sqlalchemy import or_
from database import session, User, FirstChapter, SecondChapter

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
            # Display when an user joins the game
            print(f"{user} has joined Nameless!")
            await user.message(nlessbot, "Welcome to Nameless!\nThere is no game here yet.\nOr maybe there is.\nAnyways, please do not delete this chat.")
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
                # Send the message
                await user.message(nlessbot, "Hmmm. Interesting.")
                # Don't accept answers during the cooldown period
                data.current_question = -1
                session.commit()
                # Wait a bit before sending another message
                await asyncio.sleep(5)
                # Start accepting answers
                data.current_question = 1
                session.commit()
                await user.message(nlessbot, "When do you think it will be released?")
            elif data.current_question == 1:
                if "half" in message["text"].lower() and "life" in message["text"].lower():
                    await user.message(nlessbot, "So... Never? I don't think so.")
                    return
                data.game_release = message["text"]
                data.current_question = 2
                session.commit()
                await user.message(nlessbot, "See you later then!")
        elif user.chapter == 2:
            data = session.query(SecondChapter).filter(or_(SecondChapter.mic_user == user, SecondChapter.button_user == user)).first()
            # Check that the button hasn't been pressed yet
            if data.button_pressed is not None:
                return
            # Message sent from the keyboard user
            if data.mic_user == user:
                # Forwarc the message to the other player
                await data.button_user.message(nlessbot, "The display updated, and now shows:\n" + message["text"].replace("\n", " "))
            # Message sent from the button user
            elif data.button_user == user:
                try:
                    number = int(message["text"])
                except ValueError:
                    return
                if number < 1 or number > 50:
                    return
                await user.message(nlessbot, f"You pressed button #{number}.")
                data.button_pressed = number
                session.commit()
                # Notify the other player that the keyboard stopped working.
                await data.mic_user.message(nlessbot, f"The keyboard suddenly vanished.")



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
    if rolled_number != 0:
        return
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


async def advance_to_chapter_two():
    """Try to match two players and advance them to chapter two."""
    # Check if at least two players are available
    available = session.query(User).filter_by(chapter=1).join(FirstChapter).filter_by(current_question=2).all()
    if len(available) < 2:
        return
    # Match the two players together
    firstplayer = available[0]
    secondplayer = available[1]
    # Advance the players to the second chapter
    firstplayer.chapter = 2
    secondplayer.chapter = 2
    # Create second chapter data
    target_number = random.randrange(0, 50) + 1
    data = SecondChapter(firstplayer, secondplayer, target_number)
    session.add(data)
    session.commit()
    # Introduce the chapter to the players
    await firstplayer.message(nlessbot, f"Look! A floating keyboard appeared!\nA small note on it reads: \"You must get them to press button #{target_number} at all costs.\"\nYou start typing on the keyboard, hoping something will happen...\n(All the messages you'll send from now on will be typed through the keyboard.)")
    await secondplayer.message(nlessbot, f"Hey! An array of fifty buttons appeared in front of you.\nThe buttons are numbered from 1 to 50.\nA small display is connected to the button array, and it currently displays a single word: \"STOP.\"\n(Type a number from 1 to 50 to press the corresponding button. You can press only a single button, so be careful! If you don't know what to press, be patient and wait for hints!)")
    # Display that two users have been matched and entered a new chapter
    print(f"{firstplayer} and {secondplayer} have advanced to Chapter Two!")


# Get the bot token from envvars
nlessbot_token = os.environ["nameless_token"]
# Create the bot
nlessbot = telepot.aio.Bot(nlessbot_token)
# Initialize the event loop
loop.create_task(MessageLoop(nlessbot, {"chat": on_message}).run_forever())
loop.create_task(call_every_x_seconds(advance_to_chapter_two, 600))
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