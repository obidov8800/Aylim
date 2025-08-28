
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'obidov8800' # O'zingizning maxfiy kalitingizni qo'ying
DEBUG = True
ALLOWED_HOSTS = ['45.138.159.149', 'aylim-platforma.uz', 'www.aylim-platforma.uz', '127.0.0.1', 'localhost']


INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'tests',
    'bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aylim_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'aylim_system.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'aylim_system.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aylim_db',       # yoki agar boshqa baza yaratsang, o‘shani
        'USER': 'aylim_user',
        'PASSWORD': 'aylimpass',  # aynan yuqorida kiritgan parol
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.StudentProfile'
LOGIN_URL = 'users:login'
LOGOUT_REDIRECT_URL = 'users:login'
DATA_UPLOAD_MAX_NUMBER_FIELDS = 3000

JAZZMIN_SETTINGS = {
    # sayt sarlavhasi
    "site_title": "Aylim Admin",
    "site_header": "Aylim",
    "site_brand": "Aylim",
    "site_logo": "your_logo.png", # Agar logotip qo'shmoqchi bo'lsangiz

    # Bosh sahifada ko'rinadigan tugmalar
    "topmenu_links": [
        # Bosh sahifaga qaytish
        {"name": "Bosh sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},

        # Zaxira qilish tugmasi
        {"name": "DB Backup", "url": "backup_db", "icon": "fas fa-database", "permissions": ["is_superuser"]},

        # Tiklash tugmasi (bu juda xavfli, faqat superuser uchun)
        {"name": "DB Restore", "url": "restore_db", "icon": "fas fa-undo", "permissions": ["is_superuser"]},

        # Loyihaga qaytish tugmasi (agar loyiha boshqa URLda bo'lsa)
        {"name": "Saytga", "url": "/", "new_window": True},
    ],

}
