from tests.models import Bildirishnoma

def notifications_context(request):
    if request.user.is_authenticated:
        unread_notifications_count = Bildirishnoma.objects.filter(user=request.user, is_read=False).count()
        # Hozircha faqat sonini olamiz, keyinroq to'liq ro'yxatni qo'shamiz
        return {'unread_notifications_count': unread_notifications_count}
    return {}