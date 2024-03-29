# Generated by Django 5.0.1 on 2024-01-13 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WeStatsAPI', '0002_remove_measurement_completion_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='measurementorder',
            name='measurement',
        ),
        migrations.AddField(
            model_name='westatsuser',
            name='user_role',
            field=models.CharField(choices=[('just_user', 'Пользователь'), ('meteorologist', 'Метеоролог'), ('r_manager', 'Менеджер'), ('r_admin', 'Админ')], default='r_admin', max_length=16, verbose_name='Роль пользователя'),
        ),
        migrations.AlterField(
            model_name='westatsuser',
            name='is_staff',
            field=models.BooleanField(default=False, verbose_name='Админ?'),
        ),
        migrations.AlterField(
            model_name='westatsuser',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status'),
        ),
    ]
