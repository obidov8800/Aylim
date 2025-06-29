# bot/handlers/user_menu.py

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext  # <--- QO'SHILDI
from bot.utils import db
from collections import defaultdict
from asgiref.sync import sync_to_async
from bot.states.auth_states import PasswordReset, SupportChat 
from bot.config import ADMIN_GROUP_ID
from bot.keyboards.reply import main_menu_keyboard, back_keyboard

router = Router()

# Bu router faqat ro'yxatdan o'tgan foydalanuvchilar uchun ishlashi kerak.
# Buni middleware orqali qilish mumkin, hozircha sodda tekshiruv qilamiz.

# bot/handlers/user_menu.py

# bot/handlers/user_menu.py

# YANGI, TO'G'RILANGAN KOD
@router.message(F.text == "📅 Dars Jadvalim")
async def show_schedule(message: types.Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Iltimos, avval /start buyrug'i orqali profilingizni bog'lang.")
        return

    # StudentProfile modelida guruh maydoni 'group' deb nomlangan
    if not user.group:
        await message.answer("Sizga guruh biriktirilmagan. Dars jadvalini ko'rish imkoni yo'q.")
        return

    schedule_list = await db.get_user_schedule(user)
    if not schedule_list:
        await message.answer("Sizning guruhingiz uchun dars jadvali topilmadi.")
        return
        
    grouped_schedule = defaultdict(list)
    for entry in schedule_list:
        grouped_schedule[entry.get_hafta_kuni_display()].append(entry)

    # XATOLIK TUZATILDI: user.guruh.name o'rniga user.group.name
    response_text = f"*{user.group.name}* guruhi uchun dars jadvali:\n"
    
    days_order = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    sorted_days = sorted(grouped_schedule.keys(), key=lambda x: days_order.index(x) if x in days_order else 99)

    for day in sorted_days:
        response_text += f"\n*📅 {day}*\n"
        sorted_lessons = sorted(grouped_schedule[day], key=lambda x: x.boshlanish_vaqti)
        for lesson in sorted_lessons:
            # DarsJadvali modelida o'qituvchi maydoni 'oqtuvchi' deb nomlangan
            teacher_info = f"({lesson.oqtuvchi.full_name})" if lesson.oqtuvchi else ""
            room_info = f"[{lesson.xona}-xona]" if lesson.xona else ""
            # DarsJadvali modelida fan maydoni 'fan' deb nomlangan
            response_text += f"`{lesson.boshlanish_vaqti}-{lesson.tugash_vaqti}` - {lesson.fan.nomi} {teacher_info} {room_info}\n"

    await message.answer(response_text, parse_mode="Markdown")

# bot/handlers/user_menu.py

# YANGI, TO'G'RILANGAN KOD
@router.message(F.text == "🔔 Xabarnomalar")
async def show_notifications(message: types.Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Iltimos, avval /start buyrug'i orqali profilingizni bog'lang.")
        return

    notifications = await db.get_user_notifications(user)
    if not notifications:
        await message.answer("Siz uchun yangi xabarnomalar mavjud emas.")
        return

    response_text = "Oxirgi 10 ta xabarnoma:\n" + ("-"*20) + "\n\n"
    
    for note in notifications:
        # XATOLIKLAR TUZATILDI:
        # - `sarlavha` yo'qligi uchun olib tashlandi.
        # - `created_at` o'rniga `yaratilgan_sana` ishlatildi.
        response_text += f"{note.matn}\n"
        response_text += f"_{note.yaratilgan_sana.strftime('%d.%m.%Y %H:%M')}_\n"
        response_text += "-"*20 + "\n\n"

    await message.answer(response_text, parse_mode="Markdown")

@router.message(F.text == "📈 Test Natijalarim")
async def show_test_results(message: types.Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Iltimos, avval /start buyrug'i orqali profilingizni bog'lang.")
        return

    results = await db.get_user_test_results(user)
    if not results:
        await message.answer("Sizda hali topshirilgan testlar mavjud emas.")
        return

    response_text = "Oxirgi 10 ta test natijalaringiz:\n" + ("-"*20) + "\n\n"
    
    for res in results:
        # XATOLIKLAR TUZATILDI:
        # test_schedule -> test
        # completion_date -> completion_time
        # questions.count() -> test.questions.count()
        test_name = res.test.title
        date = res.completion_time.strftime('%d.%m.%Y %H:%M') # Sana va vaqtni birga chiqaramiz
        score = res.score
        
        # Savollar sonini test orqali olamiz
        total_questions_count = await sync_to_async(res.test.questions.count)()
        percentage = (score / total_questions_count * 100) if total_questions_count > 0 else 0
        
        response_text += f"*{test_name}*\n"
        response_text += f"Sana: _{date}_\n"
        response_text += f"Natija: *{score}/{total_questions_count}* ({percentage:.2f}%)\n"
        response_text += "-"*20 + "\n\n"

    await message.answer(response_text, parse_mode="Markdown")

@router.message(F.text == "🔒 Parolni Yangilash")
async def reset_password_via_button(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Foydalanuvchi tizimda mavjudligini tekshiramiz
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Bu funksiyadan foydalanish uchun /start buyrug'i orqali profilingizni botga bog'lang.")
        return

    # Agar topilsa, parolni yangilash jarayonini boshlaymiz
    await state.update_data(user_pk=user.pk)
    await message.answer(
        "Siz parolni yangilash jarayonini boshladingiz.\n\n"
        "Iltimos, yangi parolni kiriting:",
        # Foydalanuvchiga qulaylik uchun menyuni vaqtincha olib turamiz
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(PasswordReset.waiting_for_new_password)

@router.message(F.text == "👨‍🔧 Texnik Bo'lim")
async def start_support_chat(message: types.Message, state: FSMContext):
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Bu funksiyadan foydalanish uchun /start buyrug'i orqali profilingizni botga bog'lang.")
        return

    await state.set_state(SupportChat.in_chat)
    await message.answer(
        "Siz texnik bo'lim bilan aloqaga chiqdingiz.\n\n"
        "Murojaatingizni shu yerga yozib yuborishingiz mumkin (matn, rasm, hujjat). "
        "Tugatish uchun '⬅️ Qaytish' tugmasini bosing.",
        reply_markup=back_keyboard
    )

# 2. Chatdan chiqish uchun handler
@router.message(SupportChat.in_chat, F.text == "⬅️ Qaytish")
async def stop_support_chat(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Muloqot yakunlandi. Siz asosiy menyudasiz.",
        reply_markup=main_menu_keyboard
    )

# 3. Chatdagi xabarlarni adminga yuborish uchun handler
@router.message(SupportChat.in_chat)
async def forward_message_to_support(message: types.Message):
    # Bizga faqat Telegram ID kerak, shuning uchun bazadan foydalanuvchini qayta olishimiz shart emas
    # lekin F.I.O va ID raqamini ko'rsatish uchun bu qulay
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    # Adminga foydalanuvchi haqida ma'lumot beramiz
    user_info = (
        f"Foydalanuvchidan xabar:\n"
        f"F.I.O: {user.full_name if user else 'Noma`lum'}\n"
        f"ID: {user.username if user else 'Noma`lum'}\n"
        f"Telegram ID: {message.from_user.id}"  # XATO TUZATILDI: user -> message
    )
    await message.bot.send_message(ADMIN_GROUP_ID, user_info)
    
    # Foydalanuvchining asl xabarini o'zgartirishsiz yuboramiz
    await message.forward(chat_id=ADMIN_GROUP_ID)
    
    # Foydalanuvchiga xabari yuborilganini tasdiqlaymiz
    await message.answer("✅ Xabaringiz yuborildi. Yana yozishingiz yoki '⬅️ Qaytish' tugmasi bilan chiqishingiz mumkin.")