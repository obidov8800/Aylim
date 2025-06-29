# bot/handlers/start_auth.py

from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.auth_states import LinkAccount
from bot.utils import db
from bot.keyboards.reply import main_menu_keyboard
from bot.config import ADMIN_GROUP_ID
from bot.states.auth_states import LinkAccount, PasswordReset
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        await message.answer(
            f"Assalomu alaykum, {user.full_name}! Asosiy menyudasiz.",
            reply_markup=main_menu_keyboard
        )
    else:
        await message.answer(
            "Assalomu alaykum! 'Aylim' o'quv platformasi botiga xush kelibsiz!\n\n"
            "Botdan foydalanish uchun avval o'z profilingizni Telegram hisobingizga bog'lashingiz kerak.\n\n"
            "Iltimos, saytdagi **ID raqamingizni (login)** kiriting:"
        )
        await state.set_state(LinkAccount.waiting_for_login_id)

@router.message(LinkAccount.waiting_for_login_id, F.text)
async def process_login_id(message: Message, state: FSMContext):
    login_id = message.text.strip()
    user = await db.find_user_by_username(login_id)
    
    if not user:
        await message.answer("❌ Xatolik: Bunday ID raqamli foydalanuvchi topilmadi. Iltimos, tekshirib qaytadan kiriting.")
        return
        
    if user.telegram_id:
        await message.answer("❌ Bu profil allaqachon boshqa Telegram hisobiga bog'langan. Adminga murojaat qiling.")
        await state.clear()
        return
        
    code = await db.set_verification_code(user.pk)
    
    # Adminga ham xabar berish (ixtiyoriy, lekin foydali)
    await message.bot.send_message(
        ADMIN_GROUP_ID,
        f"Foydalanuvchi {user.full_name} ({user.username}) botga ulanishga harakat qilmoqda. Tasdiqlash kodi: {code}"
    )

    await state.update_data(user_pk=user.pk)
    await state.set_state(LinkAccount.waiting_for_verification_code)
    
    await message.answer(
        "✅ Profilingiz topildi!\n\n"
        "Shaxsingizni tasdiqlash uchun, **saytdagi shaxsiy kabinetingizga** yuborilgan 6 xonali maxfiy kodni kiriting."
    )

# YANGI, TO'G'RILANGAN KOD
@router.message(LinkAccount.waiting_for_verification_code, F.text)
async def process_verification_code(message: Message, state: FSMContext):
    entered_code = message.text.strip()
    user_data = await state.get_data()
    user_pk = user_data.get('user_pk')

    if not user_pk:
        await message.answer("Xatolik yuz berdi. Iltimos, jarayonni /start buyrug'i orqali boshidan boshlang.")
        await state.clear()
        return

    # To'g'ridan-to'g'ri pk orqali foydalanuvchini olamiz (bu ancha samarali)
    user = await db.get_user_by_pk(user_pk)

    if user and user.telegram_verification_code == entered_code:
        # Agar kod to'g'ri bo'lsa, profilni telegramga bog'laymiz
        await db.link_telegram_account(user.pk, message.from_user.id)
        
        await message.answer(
            f"🎉 Tabriklaymiz, {user.full_name}! Sizning Telegram hisobingiz profilingizga muvaffaqiyatli bog'landi!",
            reply_markup=main_menu_keyboard
        )
        await state.clear() # Jarayon tugadi, holatni tozalaymiz
    else:
        # Agar kod xato bo'lsa
        await message.answer("❌ Kod xato kiritildi. Iltimos, saytdagi kodingizni tekshirib, qaytadan urinib ko'ring.")

@router.message(Command('reset_password'))
async def cmd_reset_password(message: Message, state: FSMContext):
    await state.clear()
    
    # Foydalanuvchi o'zining telegram akkauntidan yozayotganini tekshiramiz
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        # Agar foydalanuvchi hali profilini botga bog'lamagan bo'lsa
        await message.answer(
            "❌ Parolni tiklash uchun avval profilingizni botga bog'lashingiz kerak.\n\n"
            "Iltimos, /start buyrug'ini bosing va yo'riqnomaga amal qiling."
        )
        return
    
    # Agar hammasi joyida bo'lsa, jarayonni boshlaymiz
    await state.update_data(user_pk=user.pk)
    await message.answer("Siz parolni yangilash jarayonini boshladingiz.\n\n"
                       "Iltimos, yangi parolni kiriting:")
    await state.set_state(PasswordReset.waiting_for_new_password)


@router.message(PasswordReset.waiting_for_new_password, F.text)
async def process_new_password(message: Message, state: FSMContext):
    # Parolning uzunligini tekshirish (ixtiyoriy, lekin tavsiya etiladi)
    if len(message.text) < 8:
        await message.answer("Xavfsizlik uchun parol kamida 8 ta belgidan iborat bo'lishi kerak. Iltimos, boshqa parol kiriting.")
        return
        
    await state.update_data(new_password=message.text)
    await message.answer("Yangi parolni tasdiqlash uchun yana bir marta kiriting:")
    await state.set_state(PasswordReset.confirm_new_password)


@router.message(PasswordReset.confirm_new_password, F.text)
async def process_confirm_password(message: Message, state: FSMContext):
    user_data = await state.get_data()
    new_password = user_data.get('new_password')

    if new_password == message.text:
        await db.reset_user_password(user_data.get('user_pk'), new_password)
        await message.answer("✅ Parolingiz muvaffaqiyatli yangilandi!")
        await state.clear()
    else:
        await message.answer("❌ Parollar bir-biriga mos kelmadi. Iltimos, /reset_password buyrug'i bilan jarayonni boshidan boshlang.")
        await state.clear()