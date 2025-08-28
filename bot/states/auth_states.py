# bot/states/auth_states.py
from aiogram.fsm.state import State, StatesGroup

class LinkAccount(StatesGroup):
    waiting_for_login_id = State()
    waiting_for_verification_code = State()

# SODDALASHTIRILGAN KLASS
class PasswordReset(StatesGroup):
    waiting_for_new_password = State()
    confirm_new_password = State()

class SupportChat(StatesGroup):
    in_chat = State()