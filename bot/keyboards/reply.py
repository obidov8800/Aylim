# bot/keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📅 Dars Jadvalim"),
            KeyboardButton(text="📈 Test Natijalarim"),
        ],
        [
            KeyboardButton(text="🔔 Xabarnomalar"),
            KeyboardButton(text="🔒 Parolni Yangilash"),
        ],
        [
            KeyboardButton(text="👨‍🔧 Texnik Bo'lim"), # <--- YANGI TUGMA
        ]
    ],
    resize_keyboard=True
)

# Chatdan chiqish uchun alohida klaviatura
back_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Qaytish")]],
    resize_keyboard=True
)