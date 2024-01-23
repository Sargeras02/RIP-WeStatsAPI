from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from Lab03_API.serializers import WeatherStationsSerializer
from Lab03_API.models import WeatherStations
from rest_framework.views import APIView
from rest_framework.decorators import api_view


class WeatherStationsList(APIView):
    model_class = WeatherStations
    serializer_class = WeatherStationsSerializer

    def get(self, request, format=None):
        """
        Возвращает список станций
        """
        stations = self.model_class.objects.all()
        serializer = self.serializer_class(stations, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Добавляет новую станцию
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WeatherStationDetails(APIView):
    model_class = WeatherStations
    serializer_class = WeatherStationsSerializer

    def get(self, request, pk, format=None):
        """
        Возвращает информацию о станции
        """
        stock = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stock)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Обновляет информацию о станции (для модератора)
        """
        stock = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stock, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Удаляет информацию о станции
        """
        stock = get_object_or_404(self.model_class, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['Put'])
def put_detail(request, pk, format=None):
    """
    Обновляет информацию об акции (для пользователя)
    """
    stock = get_object_or_404(WeatherStations, pk=pk)
    serializer = WeatherStationsSerializer(stock, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)