from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission


# Класс метеостанции
class WeatherStation(models.Model):
    station_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    open_date = models.DateTimeField()
    description = models.TextField()
    status = models.BooleanField()
    image_url = models.CharField(max_length=255, default='https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Wetterstation01.jpeg/330px-Wetterstation01.jpeg')


# Класс измерений
class Measurement(models.Model):
    measurement_id = models.AutoField(primary_key=True)
    weather_station = models.ForeignKey('WeatherStation', on_delete=models.CASCADE, default=1)
    creator = models.ForeignKey('WeStatsUser', on_delete=models.CASCADE, related_name='created_measurements', default=1)
    created_date = models.DateTimeField(default=timezone.now)
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)


# Заказ на снятие показаний станции
class OrderInfo(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('deleted', 'Удалено'),
        ('formed', 'Сформировано'),
        ('completed', 'Добавлено'),
        ('rejected', 'Отклонено'),
    )

    order_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    creator = models.ForeignKey('WeStatsUser', on_delete=models.CASCADE, related_name='created_order', default=1)
    moderator = models.ForeignKey('WeStatsUser', on_delete=models.CASCADE, related_name='moderated_order', null=True)
    created_date = models.DateTimeField(default=timezone.now)
    formation_date = models.DateTimeField(null=True, default=None)
    completion_date = models.DateTimeField(null=True, default=None)


# Класс связи измерение-заказ
class OrderItemMeasurement(models.Model):
    order = models.ForeignKey('OrderInfo', on_delete=models.CASCADE)
    measurement = models.ForeignKey('Measurement', on_delete=models.CASCADE)
    comp_id = models.UniqueConstraint(fields=['order', 'measurement'], name='composite_pk_constraint')


# "Красивый" заказ
class TotalOrderInfo:
    def __init__(self, order, measurements):
        self.order = order
        self.measurements = measurements


# Менеджер пользователей
class WeStatsUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('user_role', 'r_admin')
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, password, **extra_fields)


# Класс пользователя
class WeStatsUser(AbstractBaseUser, PermissionsMixin):
    ROLES_CHOICES = (
        ('just_user', 'Пользователь'),
        ('meteorologist', 'Метеоролог'),
        ('r_manager', 'Менеджер'),
        ('r_admin', 'Админ'),
    )

    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(max_length=50, verbose_name="Пароль")
    user_role = models.CharField(max_length=16, choices=ROLES_CHOICES, default='just_user', verbose_name="Роль пользователя")
    is_staff = models.BooleanField(default=False, verbose_name='Админ?')
    name = models.CharField(max_length=50, verbose_name="Имя", default='Noname')

    # Для автоматического управления пользователями
    objects = WeStatsUserManager()

    USERNAME_FIELD = 'email'

    groups = models.ManyToManyField(Group, related_name='we_stats_user_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='we_stats_user_permissions')


# >> OBSOLETE
# Класс М-М станция-измерение
class StationsMeasurements(models.Model):
    weather_station = models.ForeignKey('WeatherStation', on_delete=models.CASCADE)
    measurement = models.ForeignKey('Measurement', on_delete=models.CASCADE)
    id = models.UniqueConstraint(fields=['weather_station', 'measurement'], name='composite_pk_constraint')