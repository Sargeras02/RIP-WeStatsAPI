from Lab03_API.models import WeatherStations
from Lab03_API.models import Measurements
from Lab03_API.models import StationsMeasurements
from Lab03_API.models import User
from rest_framework import serializers


class WeatherStationsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = WeatherStations
        # Поля, которые мы сериализуем
        fields = ["station_id", "name", "location", "opendate", "description", 'status', 'image_url']
