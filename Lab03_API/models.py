from django.db import models
from django.utils import timezone


class WeatherStations(models.Model):
    station_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    opendate = models.DateTimeField()
    description = models.TextField()
    status = models.BooleanField()
    image_url = models.CharField(max_length=255, default='no_image.png')


class Measurements(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('deleted', 'Удалено'),
        ('formed', 'Сформировано'),
        ('completed', 'Добавлено'),
        ('rejected', 'Отклонено'),
    )
    measurement_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    creator = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_measurements', default=1)
    moderator = models.ForeignKey('User', on_delete=models.CASCADE, related_name='moderated_measurements', null=True)
    created_date = models.DateField(default=timezone.now)
    formation_date = models.DateField(default=timezone.now)
    completion_date = models.DateField(default=timezone.now)
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)


class StationsMeasurements(models.Model):
    weatherStations = models.ForeignKey('WeatherStations', on_delete=models.CASCADE)
    measurement = models.ForeignKey('Measurements', on_delete=models.CASCADE)
    id = models.UniqueConstraint(fields=['weatherStations', 'measurement'], name='composite_pk_constraint')


class User(models.Model):
    ROLES_CHOICES = (
        ('visitor', 'Посетитель'),
        ('meteoUser', 'Метеоролог'),
        ('moder', 'Модератор'),
    )
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16, choices=ROLES_CHOICES, default='visitor')
