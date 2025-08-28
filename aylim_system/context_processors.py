# aylim_system/context_processors.py

from tests.models import Bildirishnoma

def notifications(request):
    """
    Saytning har bir sahifasi uchun o'qilmagan bildirishnomalar
    sonini kontekstga qo'shib beradi.
    """
    if request.user.is_authenticated:
        # Model maydonlariga moslashtirildi ('user', 'is_read')
        count = Bildirishnoma.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}