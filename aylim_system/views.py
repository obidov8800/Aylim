from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import connection
from django.conf import settings
import os
import datetime
import subprocess

# PostgreSQL buyruqlarining to'liq yo'lini aniqlang
# Bu sizning tizimingizdagi PostgreSQL versiyasiga qarab o'zgarishi mumkin
POSTGRES_BIN_PATH = "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" 
PG_DUMP_PATH = os.path.join(POSTGRES_BIN_PATH, "pg_dump.exe")
PSQL_PATH = os.path.join(POSTGRES_BIN_PATH, "psql.exe")


@staff_member_required
def backup_db_view(request):
    """
    Ma'lumotlar bazasini zaxira qilish uchun view.
    POST so'rovi kelsa backup qiladi, GET so'rovi kelsa sahifani ko'rsatadi.
    """
    if request.method == 'POST':
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings.get('PASSWORD', '')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', 5432)

        # Zaxira papkasini yaratish. Loyiha papkasida 'db_backups'
        backup_dir = os.path.join(settings.BASE_DIR, 'db_backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Fayl nomini va yo'lini yaratish
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"{db_name}_backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            command = [
                PG_DUMP_PATH,
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-F', 'c',  # Custom format
                '-f', backup_path,
            ]
            
            # Subprocess orqali buyruqni bajarish
            result = subprocess.run(command, env=env, check=True, text=True, capture_output=True)
            messages.success(request, f"Ma'lumotlar bazasi muvaffaqiyatli zaxira qilindi: {backup_filename}")

        except FileNotFoundError:
            messages.error(request, f"Xatolik: '{PG_DUMP_PATH}' buyrug'i topilmadi. PostgreSQL bin papkasini to'g'ri ko'rsating.")
        except subprocess.CalledProcessError as e:
            messages.error(request, f"Zaxira qilishda xatolik yuz berdi: {e.stderr}")
        finally:
            if 'PGPASSWORD' in env:
                del env['PGPASSWORD']
        
        return render(request, 'backup_page.html', {'backups': os.listdir(backup_dir)})

    # GET so'rovi uchun shablonni ko'rsatish
    backup_dir = os.path.join(settings.BASE_DIR, 'db_backups')
    backups = []
    if os.path.exists(backup_dir):
        # Eng yangi fayllarni birinchi ko'rsatish uchun saralash
        backups = sorted(os.listdir(backup_dir), reverse=True)
    
    return render(request, 'backup_page.html', {'backups': backups})


@staff_member_required
def restore_db_view(request):
    """
    Ma'lumotlar bazasini tiklash uchun view.
    POST so'rovi kelsa backup faylini tiklaydi, GET kelsa sahifani ko'rsatadi.
    """
    backup_dir = os.path.join(settings.BASE_DIR, 'db_backups')
    
    if request.method == 'POST':
        backup_file = request.POST.get('backup_file')
        if not backup_file:
            messages.error(request, "Tiklash uchun fayl tanlanmadi.")
            return render(request, 'restore_page.html')

        backup_path = os.path.join(backup_dir, backup_file)
        if not os.path.exists(backup_path):
            messages.error(request, f"Xatolik: {backup_file} nomli zaxira fayli topilmadi.")
            return render(request, 'restore_page.html')
            
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings.get('PASSWORD', '')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', 5432)

        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            # Tiklash buyrug'i: avval barcha ulanishlarni o'chiramiz
            kill_connections_command = [
                PSQL_PATH,
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', 'postgres', # 'postgres' ma'lumotlar bazasiga ulanib, asosiy bazani o'chirish
                '-c', f"REVOKE CONNECT ON DATABASE {db_name} FROM public; SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_name}';"
            ]
            subprocess.run(kill_connections_command, env=env, check=True)

            # Bazani qayta yaratish
            drop_db_command = [PSQL_PATH, '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', 'postgres', '-c', f"DROP DATABASE {db_name};"]
            subprocess.run(drop_db_command, env=env, check=True)

            create_db_command = [PSQL_PATH, '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', 'postgres', '-c', f"CREATE DATABASE {db_name};"]
            subprocess.run(create_db_command, env=env, check=True)

            # Backup faylini tiklash
            restore_command = [
                PSQL_PATH,
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-f', backup_path,
            ]
            subprocess.run(restore_command, env=env, check=True, text=True, capture_output=True)
            
            messages.success(request, f"Ma'lumotlar bazasi '{backup_file}' faylidan muvaffaqiyatli tiklandi.")
        
        except FileNotFoundError:
            messages.error(request, f"Xatolik: '{PSQL_PATH}' buyrug'i topilmadi. PostgreSQL bin papkasini to'g'ri ko'rsating.")
        except subprocess.CalledProcessError as e:
            messages.error(request, f"Tiklashda xatolik yuz berdi: {e.stderr}")
        finally:
            if 'PGPASSWORD' in env:
                del env['PGPASSWORD']

        return render(request, 'restore_page.html', {'backups': sorted(os.listdir(backup_dir), reverse=True)})
    
    # GET so'rovi uchun shablonni ko'rsatish
    backups = []
    if os.path.exists(backup_dir):
        backups = sorted(os.listdir(backup_dir), reverse=True)
        
    return render(request, 'restore_page.html', {'backups': backups})