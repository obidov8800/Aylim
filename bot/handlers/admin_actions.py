# bot/handlers/admin_actions.py

from aiogram import Router, F, types
from bot.config import ADMIN_GROUP_ID

router = Router()

# Bu handler faqat adminlar guruhida ishlaydi
@router.message(F.chat.id == ADMIN_GROUP_ID, F.reply_to_message)
async def reply_from_admin_to_user(message: types.Message):
    """
    Bu funksiya admin guruhidagi "reply" (javob) qilingan xabarlarni ushlaydi
    va o'sha javobni asl foydalanuvchiga yuboradi.
    """
    
    # Foydalanuvchining asl xabari (admin javob qaytarayotgan xabar)
    replied_message = message.reply_to_message
    
    # Agar admin foydalanuvchidan forward qilingan xabarga javob bersa
    if replied_message.forward_from:
        original_user_id = replied_message.forward_from.id
        
        # Adminning javobini asl foydalanuvchiga yuborish
        try:
            # Agar admin matn yozgan bo'lsa
            if message.text:
                await message.bot.send_message(
                    chat_id=original_user_id,
                    text=f"👨‍🔧 Texnik bo'limdan javob:\n\n{message.text}"
                )
            # Agar admin rasm, hujjat va hk. yuborgan bo'lsa
            else:
                # To'g'ridan-to'g'ri nusxasini yuborish
                await message.copy_to(chat_id=original_user_id)

            await message.reply("✅ Javobingiz foydalanuvchiga muvaffaqiyatli yuborildi.")

        except Exception as e:
            await message.reply(f"❌ Xatolik: Javobni yuborib bo'lmadi.\nSabab: {e}")
            
    # Agar admin botning "Foydalanuvchidan xabar:" degan servis xabariga javob bersa
    elif replied_message.from_user.is_bot:
        # Xabar matnidan foydalanuvchi ID'sini ajratib olamiz
        try:
            # Xabar matni: "...\nTelegram ID: 12345678"
            user_id_line = [line for line in replied_message.text.split('\n') if "Telegram ID:" in line]
            if user_id_line:
                original_user_id = int(user_id_line[0].split(':')[1].strip())
                
                # Adminning javobini yuborish
                if message.text:
                    await message.bot.send_message(
                        chat_id=original_user_id,
                        text=f"👨‍🔧 Texnik bo'limdan javob:\n\n{message.text}"
                    )
                else:
                    await message.copy_to(chat_id=original_user_id)
                    
                await message.reply("✅ Javobingiz foydalanuvchiga muvaffaqiyatli yuborildi.")
            else:
                # Agar servis xabarida ID topilmasa (ehtimoldan yiroq)
                await message.reply("⚠️ Ushbu xabardan foydalanuvchi ID'sini topib bo'lmadi.")
        except Exception as e:
            await message.reply(f"❌ Xatolik: Javobni yuborib bo'lmadi.\nSabab: {e}")