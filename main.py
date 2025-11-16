import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION - EDIT THESE ==========
BOT_TOKEN = "8592044424:AAFGztD6u3O1OMxIiooIyKXT_7sVgGBVVq4"  # From @BotFather
ADMIN_CHAT_ID = "1081694677"  # From @userinfobot

# Turf Details
TURF_NAME = "PITCH PERFECT TURF"
TURF_ADDRESS = "Near Sai Baba Kovil, Aruppukottai"
CONTACT_NUMBER = "+91 73588 48765"

# Pricing
FULL_GROUND_PRICE = 500
HALF_GROUND_PRICE = 250

# Time slots (7 AM to 11:59 PM, 1-hour slots)
TIME_SLOTS = [
    "07:00 AM - 08:00 AM", "08:00 AM - 09:00 AM", "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM",
    "01:00 PM - 02:00 PM", "02:00 PM - 03:00 PM", "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM",
    "07:00 PM - 08:00 PM", "08:00 PM - 09:00 PM", "09:00 PM - 10:00 PM",
    "10:00 PM - 11:00 PM", "11:00 PM - 11:59 PM"
]

# Ground types
GROUND_TYPES = {"full": "Full Ground", "half": "Half Ground"}

# Database (in-memory for now)
bookings_db = {}
user_sessions = {}

# ========== HELPER FUNCTIONS ==========


def get_next_days(days=2):
    """Get next N days for booking"""
    dates = []
    for i in range(days + 1):  # Include today
        date = datetime.now() + timedelta(days=i)
        dates.append(date.strftime("%d/%m/%Y"))
    return dates


def is_slot_available(date, slot, ground_type):
    """Check if slot is available"""
    booking_key = f"{date}_{slot}_{ground_type}"
    return booking_key not in bookings_db


def create_booking(date, slot, ground_type, user_data):
    """Create a new booking"""
    booking_id = f"PPT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    booking_key = f"{date}_{slot}_{ground_type}"

    price = FULL_GROUND_PRICE if ground_type == "full" else HALF_GROUND_PRICE

    bookings_db[booking_key] = {
        'booking_id': booking_id,
        'date': date,
        'slot': slot,
        'ground_type': GROUND_TYPES[ground_type],
        'name': user_data.get('name'),
        'phone': user_data.get('phone'),
        'sport': user_data.get('sport'),
        'amount': price,
        'status': 'confirmed',
        'user_id': user_data.get('user_id'),
        'created_at': datetime.now().isoformat()
    }

    return booking_id, bookings_db[booking_key]


# ========== COMMAND HANDLERS ==========


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Welcome message"""
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("⚽ Book a Slot", callback_data="book_slot")],
        [InlineKeyboardButton("📋 My Bookings", callback_data="my_bookings")],
        [InlineKeyboardButton("📞 Contact Us", callback_data="contact")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""
⚽ *Welcome to {TURF_NAME}!* 🏏

Hi {user.first_name}! 👋

Book your Football & Cricket slots instantly at {TURF_NAME}!

✅ Real-time availability
✅ Full Ground & Half Ground options
✅ 1-hour slot bookings
✅ Open 7 AM - 11:59 PM

💰 Pricing:
• Full Ground: ₹{FULL_GROUND_PRICE}/hour
• Half Ground: ₹{HALF_GROUND_PRICE}/hour

Choose an option below to get started:
    """

    await update.message.reply_text(welcome_text,
                                    parse_mode='Markdown',
                                    reply_markup=reply_markup)


async def admin_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command - View today's bookings"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ This command is only for admins.")
        return

    today = datetime.now().strftime("%d/%m/%Y")
    today_bookings = [
        b for key, b in bookings_db.items() if b['date'] == today
    ]

    if not today_bookings:
        await update.message.reply_text(f"📅 No bookings for today ({today})")
        return

    text = f"📅 *Today's Bookings - {TURF_NAME}*\n{today}\n\n"
    for i, booking in enumerate(today_bookings, 1):
        text += f"{i}. *{booking['slot']}*\n"
        text += f"   🎫 {booking['booking_id']}\n"
        text += f"   🏟️ {booking['ground_type']}\n"
        text += f"   👤 {booking['name']}\n"
        text += f"   📱 {booking['phone']}\n"
        text += f"   {booking['sport']}\n"
        text += f"   💰 ₹{booking['amount']}\n\n"

    await update.message.reply_text(text, parse_mode='Markdown')


async def admin_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command - View all bookings"""
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ This command is only for admins.")
        return

    if not bookings_db:
        await update.message.reply_text("📋 No bookings yet!")
        return

    text = f"📋 *All Bookings - {TURF_NAME}*\n\n"
    for i, (key, booking) in enumerate(bookings_db.items(), 1):
        text += f"{i}. {booking['date']} | {booking['slot']}\n"
        text += f"   🎫 {booking['booking_id']}\n"
        text += f"   🏟️ {booking['ground_type']} | {booking['name']}\n\n"
        if i % 10 == 0:  # Send in batches to avoid message length limit
            await update.message.reply_text(text, parse_mode='Markdown')
            text = ""

    if text:
        await update.message.reply_text(text, parse_mode='Markdown')


# ========== CALLBACK HANDLERS ==========


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        user_sessions[user_id] = {}

    # Book Slot Flow
    if data == "book_slot":
        keyboard = [[
            InlineKeyboardButton("⚽ Football", callback_data="sport_football")
        ], [InlineKeyboardButton("🏏 Cricket", callback_data="sport_cricket")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"⚽🏏 *Book Your Slot at {TURF_NAME}*\n\nSelect Sport:",
            parse_mode='Markdown',
            reply_markup=reply_markup)

    elif data.startswith("sport_"):
        sport = "⚽ Football" if data == "sport_football" else "🏏 Cricket"
        user_sessions[user_id]['sport'] = sport

        keyboard = [[
            InlineKeyboardButton("🏟️ Full Ground (₹300)",
                                 callback_data="ground_full")
        ],
                    [
                        InlineKeyboardButton("⚡ Half Ground (₹150)",
                                             callback_data="ground_half")
                    ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Selected: {sport}\n\n🏟️ *Select Ground Type:*",
            parse_mode='Markdown',
            reply_markup=reply_markup)

    elif data.startswith("ground_"):
        ground_type = data.replace("ground_", "")
        user_sessions[user_id]['ground_type'] = ground_type
        ground_name = GROUND_TYPES[ground_type]
        price = FULL_GROUND_PRICE if ground_type == "full" else HALF_GROUND_PRICE

        dates = get_next_days(2)
        keyboard = []
        for date in dates:
            label = "Today" if date == dates[
                0] else "Tomorrow" if date == dates[1] else date
            keyboard.append([
                InlineKeyboardButton(f"📅 {label} ({date})",
                                     callback_data=f"date_{date}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Selected: {ground_name} (₹{price})\n\n📅 *Select Date:*\n(Advance booking: 2 days)",
            parse_mode='Markdown',
            reply_markup=reply_markup)

    elif data.startswith("date_"):
        date = data.replace("date_", "")
        user_sessions[user_id]['date'] = date
        ground_type = user_sessions[user_id]['ground_type']

        keyboard = []
        for slot in TIME_SLOTS:
            status = "✅" if is_slot_available(date, slot, ground_type) else "❌"
            if status == "✅":
                keyboard.append([
                    InlineKeyboardButton(f"{status} {slot}",
                                         callback_data=f"slot_{slot}")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(f"{status} {slot} (Booked)",
                                         callback_data="slot_booked")
                ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        ground_name = GROUND_TYPES[ground_type]
        await query.edit_message_text(
            f"📅 Date: {date}\n🏟️ {ground_name}\n\n⏰ *Select Time Slot:*",
            parse_mode='Markdown',
            reply_markup=reply_markup)

    elif data.startswith("slot_") and data != "slot_booked":
        slot = data.replace("slot_", "")
        user_sessions[user_id]['slot'] = slot

        ground_type = user_sessions[user_id]['ground_type']
        price = FULL_GROUND_PRICE if ground_type == "full" else HALF_GROUND_PRICE

        text = f"""
📋 *Booking Details:*

{user_sessions[user_id]['sport']}
🏟️ Ground: {GROUND_TYPES[ground_type]}
📅 Date: {user_sessions[user_id]['date']}
⏰ Time: {slot}
💰 Price: ₹{price}

Please enter your *full name*:
        """

        user_sessions[user_id]['step'] = 'awaiting_name'
        await query.edit_message_text(text, parse_mode='Markdown')

    elif data == "slot_booked":
        await query.answer(
            "⚠️ This slot is already booked. Please select another.",
            show_alert=True)

    elif data == "confirm_booking":
        user_id = update.effective_user.id
        session = user_sessions.get(user_id, {})

        booking_id, booking = create_booking(session['date'], session['slot'],
                                             session['ground_type'], session)

        confirmation = f"""
✅ *BOOKING CONFIRMED!* 🎉

🎫 *Booking ID:* {booking_id}
━━━━━━━━━━━━━━━━━━━━

👤 Name: {booking['name']}
📱 Phone: {booking['phone']}
{booking['sport']}
🏟️ Ground: {booking['ground_type']}
📅 Date: {booking['date']}
⏰ Time: {booking['slot']}

💰 *Amount: ₹{booking['amount']}*
💳 Pay at turf counter

📍 *{TURF_NAME}*
{TURF_ADDRESS}
📞 {CONTACT_NUMBER}

⚠️ Please show this message at the turf entrance.

See you at the pitch! ⚽🏏
        """

        await query.edit_message_text(confirmation, parse_mode='Markdown')

        # Notify admin
        admin_msg = f"""
🔔 *NEW BOOKING - {TURF_NAME}!*

🎫 {booking_id}
📅 {booking['date']} | {booking['slot']}
🏟️ {booking['ground_type']}
👤 {booking['name']}
📱 {booking['phone']}
{booking['sport']}
💰 ₹{booking['amount']} (Pay at counter)
        """

        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                           text=admin_msg,
                                           parse_mode='Markdown')
        except:
            logger.error("Could not send admin notification")

        user_sessions.pop(user_id, None)

    elif data == "my_bookings":
        user_bookings = [
            b for b in bookings_db.values() if b.get('user_id') == user_id
        ]

        if not user_bookings:
            await query.edit_message_text(
                "📋 You don't have any bookings yet.\n\n"
                f"Click /start to book your slot at {TURF_NAME}!")
        else:
            text = f"📋 *Your Bookings at {TURF_NAME}:*\n\n"
            for booking in user_bookings:
                text += f"🎫 {booking['booking_id']}\n"
                text += f"📅 {booking['date']} | {booking['slot']}\n"
                text += f"🏟️ {booking['ground_type']}\n"
                text += f"{booking['sport']}\n\n"
            await query.edit_message_text(text, parse_mode='Markdown')

    elif data == "contact":
        contact_text = f"""
📞 *Contact {TURF_NAME}*

📍 *Address:*
{TURF_ADDRESS}

📱 *Phone:*
{CONTACT_NUMBER}

⏰ *Timings:*
7:00 AM - 11:59 PM (Daily)

💰 *Pricing:*
• Full Ground: ₹{FULL_GROUND_PRICE}/hour
• Half Ground: ₹{HALF_GROUND_PRICE}/hour

🎯 *Sports Available:*
⚽ Football | 🏏 Cricket

Click /start to book now!
        """
        await query.edit_message_text(contact_text, parse_mode='Markdown')

    elif data == "help":
        help_text = f"""
ℹ️ *How to Book at {TURF_NAME}:*

1️⃣ Click "Book a Slot"
2️⃣ Select sport (Football/Cricket)
3️⃣ Choose ground type (Full/Half)
4️⃣ Pick date and time
5️⃣ Enter your details
6️⃣ Confirm booking
7️⃣ Pay at turf counter

💡 *Features:*
✅ Real-time slot availability
✅ Instant booking confirmation
✅ Advance booking (2 days)
✅ 1-hour slot duration

⏰ *Timings:*
7:00 AM - 11:59 PM

💰 *Pricing:*
• Full Ground: ₹{FULL_GROUND_PRICE}
• Half Ground: ₹{HALF_GROUND_PRICE}

📞 *Support:* {CONTACT_NUMBER}

Need help? Click /start
        """
        await query.edit_message_text(help_text, parse_mode='Markdown')


# ========== MESSAGE HANDLERS ==========


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (name and phone)"""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        await update.message.reply_text(
            f"Please start by clicking /start\n\nWelcome to {TURF_NAME}!")
        return

    session = user_sessions[user_id]

    # Awaiting name
    if session.get('step') == 'awaiting_name':
        session['name'] = text
        session['step'] = 'awaiting_phone'
        await update.message.reply_text(
            "✅ Name saved!\n\nNow enter your *phone number* (10 digits):",
            parse_mode='Markdown')

    # Awaiting phone
    elif session.get('step') == 'awaiting_phone':
        if len(text) != 10 or not text.isdigit():
            await update.message.reply_text(
                "⚠️ Please enter a valid 10-digit phone number:")
            return

        session['phone'] = text
        session['user_id'] = user_id

        ground_type = session['ground_type']
        price = FULL_GROUND_PRICE if ground_type == "full" else HALF_GROUND_PRICE

        # Show booking summary
        summary = f"""
✅ *Booking Summary - {TURF_NAME}*

👤 Name: {session['name']}
📱 Phone: {session['phone']}
{session['sport']}
🏟️ Ground: {GROUND_TYPES[ground_type]}
📅 Date: {session['date']}
⏰ Time: {session['slot']}

💰 *Amount: ₹{price}*
💳 Pay at turf counter

Confirm your booking:
        """

        keyboard = [[
            InlineKeyboardButton("✅ Confirm Booking",
                                 callback_data="confirm_booking")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(summary,
                                        parse_mode='Markdown',
                                        reply_markup=reply_markup)


# ========== MAIN FUNCTION ==========


def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", admin_today))
    application.add_handler(CommandHandler("all", admin_all))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(button_handler))

    # Message handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start bot
    logger.info(f"🤖 {TURF_NAME} Bot started successfully!")
    logger.info(f"📍 Location: {TURF_ADDRESS}")
    logger.info(f"📞 Contact: {CONTACT_NUMBER}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
