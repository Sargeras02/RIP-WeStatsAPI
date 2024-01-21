from rest_framework import serializers
from .models import (WeatherStation, Measurement,
                     OrderInfo, OrderItemMeasurement, TotalOrderInfo,
                     WeStatsUser)


class WeatherStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherStation
        fields = ['station_id', 'name', 'description', 'location', 'open_date', 'status', 'image_url']


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ['measurement_id', 'weather_station',
                  'creator', 'created_date',
                  'temperature', 'humidity', 'wind_speed']


class UploadMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ['weather_station',
                  'temperature', 'humidity', 'wind_speed']


class MeasurementDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ['weather_station', 'created_date',
                  'temperature', 'humidity', 'wind_speed']


class InitOrderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ['creator']


class PublicOrderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ['order_id', 'status', 'creator', 'formation_date', 'completion_date']


class OrderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ['order_id', 'status', 'creator', 'moderator', 'created_date', 'formation_date', 'completion_date']


class OrderItemMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemMeasurement
        fields = ['order', 'measurement']


class OrderAddItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemMeasurement
        fields = ['measurement_id']


class TotalOrderInfoSerializer(serializers.Serializer):
    order = PublicOrderInfoSerializer()
    measurements = serializers.ListField(child=MeasurementDataSerializer())

    def create(self, validated_data):
        order_data = validated_data.pop('order')
        measurements_data = validated_data.pop('measurements')
        order = TotalOrderInfo(order=order_data, measurements=measurements_data)
        return order

    def update(self, instance, validated_data):
        instance.order = validated_data.get('order', instance.order)
        instance.measurements = validated_data.get('measurements', instance.measurements)
        return instance


class WeStatsUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeStatsUser
        fields = ['user_id', 'name', 'email', 'password', 'user_role', 'is_staff', 'is_superuser']


class WeStatsUserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeStatsUser
        fields = ['email', 'password']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeStatsUser
        fields = ['name', 'role', 'email']

    ROLES_CHOICES = WeStatsUser.ROLES_CHOICES
    role = serializers.SerializerMethodField()

    def get_role(self, instance):
        return dict(self.ROLES_CHOICES).get(instance.user_role)


class WeStatsUserUpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeStatsUser
        fields = ['user_role']


# >> OBSOLETE
'''class StationsMeasurementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationsMeasurements
        fields = ['weatherStations', 'measurement']'''