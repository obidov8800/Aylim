# Generated by Django 5.2.1 on 2025-06-22 15:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_alter_attendancerecord_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentanswer',
            name='selected_answer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tests.answeroption'),
        ),
    ]
