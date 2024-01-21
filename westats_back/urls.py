from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from WeStatsAPI.views import (
    WeatherStationList, WeatherStationDetail,
    MeasurementsList, MeasurementsDetail,
    OrderInfoList, OrderUserList, OrderUserCurrent, OrderDetail, AddOrderItem,
    OrderFormat, OrderDelete, OrderAccept, OrderReject,
    WeStatUserViewSet,
    login_view, logout_view, profile_view, update_user_role_view
)

router = routers.DefaultRouter()
router.register(r'users', WeStatUserViewSet, basename='users')

schema_view = get_schema_view(
   openapi.Info(
      title="WeStats API",
      default_version='v1',
      description="WeStats - Weather Service API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=([permissions.AllowAny,]),
)

urlpatterns = [
    path('', include(router.urls)),

    # WeatherStation URLs
    path('stations', WeatherStationList.as_view(), name='weather_station_list'),
    path('stations/<int:pk>', WeatherStationDetail.as_view(), name='weather_station_detail'),

    # Measurements URLs
    path('measurements', MeasurementsList.as_view(), name='measurements_list'),
    path('measurements/<int:pk>', MeasurementsDetail.as_view(), name='measurement_detail'),

    # ?filter=... + cookie outdate
    # Orders URLs
    path('orders', OrderInfoList.as_view(), name='orders_list'),
    path('orders/<int:pk>', OrderDetail.as_view(), name='order_detail'),
    path('orders/<int:pk>/format', OrderFormat.as_view(), name='order_format'),
    path('orders/<int:pk>/delete', OrderDelete.as_view(), name='order_delete'),
    path('orders/<int:pk>/accept', OrderAccept.as_view(), name='order_accept'),
    path('orders/<int:pk>/reject', OrderReject.as_view(), name='order_reject'),
    path('orders/<int:pk>/addItem', AddOrderItem.as_view(), name='order_add_item'),
    path('userorders', OrderUserList.as_view(), name='order_user_list'),
    path('userorders/current', OrderUserCurrent.as_view(), name='order_user_current'),

    path('api-auth', include('rest_framework.urls', namespace='rest_framework')),
    path('login',  login_view, name='login'),
    path('logout', logout_view, name='logout'),
    path('profile', profile_view, name='profile'),
    path('update_user_role/<int:pk>', update_user_role_view, name='update_user_role'),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin', admin.site.urls),

    # >> OBSOLETE

    # StationsMeasurements URLs
    # path('stat_measures/', StationsMeasurementsList.as_view(), name='stations_measurements_list'),
    # path('stat_measures/<int:pk>/', StationsMeasurementsDetail.as_view(), name='stations_measurement_detail'),

    # WeStatsUser URLs
    # path('users/', WeStatUserViewSet.as_view(), name='user_list'),
    # path('users/<int:pk>/', WeStatsUserDetail.as_view(), name='user_detail'),
]
