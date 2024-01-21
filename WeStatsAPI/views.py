import requests
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets

from .minio import add_pic
from .serializers import (WeatherStationSerializer, MeasurementSerializer, UploadMeasurementSerializer,
                          OrderInfoSerializer, InitOrderInfoSerializer, OrderAddItemSerializer,
                          OrderItemMeasurementSerializer, TotalOrderInfoSerializer,
                          WeStatsUserSerializer, WeStatsUserLoginSerializer, ProfileSerializer, WeStatsUserUpdateRoleSerializer)
from .models import (WeatherStation, Measurement,
                     OrderInfo, OrderItemMeasurement, TotalOrderInfo,
                     WeStatsUser)

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .permissions import (IsAdmin, IsManager, IsMeteorologist, ManagerOrMeteo)

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import (AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly)
from django.views.decorators.csrf import csrf_exempt

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from .parameters import (CookieParameter, RoleParameter, PicParameter, FilterParameter)

# filters
from django.db.models import Q

# REDIS
from django.conf import settings
import uuid
import redis
# sudo service redis-server start

# Redis
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

# Custom decorator для permission/def
# OBSOLETE
def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator


# >> Login Section
class WeStatUserViewSet(viewsets.ModelViewSet):
    queryset = WeStatsUser.objects.all()
    serializer_class = WeStatsUserSerializer
    model_class = WeStatsUser

    #@permission_classes([AllowAny])
    #@authentication_classes([])
    @csrf_exempt
    def create(self, request):
        """
        Функция регистрации новых пользователей

        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(email=serializer.data['email'],
                                                 password=serializer.data['password'],
                                                 user_role=serializer.data['user_role'],
                                                 is_superuser=serializer.data['is_superuser'],
                                                 is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        permission_classes = [AllowAny]
        '''if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]'''
        return [permission() for permission in permission_classes]


#@permission_classes([AllowAny])
#@authentication_classes([])
@csrf_exempt
@swagger_auto_schema(method='POST',
                     request_body=WeStatsUserLoginSerializer,
                     responses={200: 'Success'})
@api_view(['POST'])
def login_view(request):
    """
    Аутентификация пользователя.

    Позволяет пользователю войти в систему, предоставив свой email и пароль.
    """
    # FORM AUTH request.POST
    email = request.data.get("email")
    password = request.data.get("password")
    user = authenticate(request, email=email, password=password)

    if user is not None:
        random_key = uuid.uuid4()
        session_storage.set(str(random_key), email)
        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)
        return response
    else:
        error_data = {'status': 'error', 'error': 'login failed'}
        return JsonResponse(error_data, status=401)


#@permission_classes([AllowAny])
#@authentication_classes([])
@swagger_auto_schema(method='POST',
                     responses={200: 'Success'},
                     manual_parameters=[CookieParameter()],)
@api_view(['POST'])
def logout_view(request):
    """
    Завершение сеанса пользователя.

    Завершает текущий сеанс пользователя, удаляя данные о сеансе из хранилища.
    """
    session_id = request.COOKIES.get("session_id")
    if session_id:
        try:
            session_data = session_storage.get(session_id)
            print(f"Session Data: {session_data}")  # Добавим эту строку для отладки
            if session_data:
                session_storage.delete(session_id)
                #logout(request._request)
                return Response({'status': 'Success'})
            else:
                return HttpResponse("Session not found in Redis.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return HttpResponse(f"Error during logout: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return HttpResponse("Session ID not found in cookies.", status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='GET',
                     responses={200: ProfileSerializer()},
                     manual_parameters=[CookieParameter()],
                     security=[{"session_id": []}])
@api_view(['GET'])
def profile_view(request):
    """
    Получение профиля пользователя.

    Возвращает информацию о текущем пользователе на основе идентификатора сессии в куках.
    """
    session_id = request.COOKIES.get("session_id")
    session = session_storage.get(session_id)
    user = WeStatsUser.objects.get(email=session.decode('utf-8'))
    serializer = ProfileSerializer(user)
    return Response(serializer.data)


#request_body=WeStatsUserUpdateRoleSerializer,
@swagger_auto_schema(method='POST',
                     responses={200: WeStatsUserSerializer()},
                     security=[{"session_id": []}],
                     manual_parameters=[CookieParameter(), RoleParameter()])
@api_view(['POST'])
def update_user_role_view(request, pk):
    """
    Обновление роли пользователя.

    Обновляет роль пользователя на основе переданного идентификатора пользователя (id) и новой роли,
    указанной в параметре запроса "role".
    """
    new_role = request.query_params.get('role')
    try:
        user = WeStatsUser.objects.get(user_id=pk)
    except WeStatsUser.DoesNotExist:
        return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    user.user_role = new_role
    if new_role == 'r_admin':
        user.is_staff = True
        user.is_superuser = True
    elif new_role == 'r_manager':
        user.is_staff = True
        user.is_superuser = False
    else:
        user.is_staff = False
        user.is_superuser = False

    user.save()
    serializer = WeStatsUserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

# << End Of Login


class WeatherStationList(APIView):
    model_class = WeatherStation
    serializer_class = WeatherStationSerializer
    parser_classes = (MultiPartParser, FormParser)

    # Список метеостанций
    @swagger_auto_schema(responses={200: WeatherStationSerializer(many=True)},
                         manual_parameters=[FilterParameter()])
    #@authentication_classes([])
    #@method_permission_classes((AllowAny,))
    def get(self, request, format=None):
        """
        Получение списка метеостанций.

        Возвращает список метеостанций с возможностью фильтрации по различным полям. Фильтр осуществляется
        на основе параметра запроса "filter", который применяется к полям "name", "location" и "description".
        """
        filter_criteria = request.query_params.get('filter')
        if filter_criteria is None:
            filter_criteria = ''
        filter_condition = (
                Q(name__icontains=filter_criteria) |
                Q(location__icontains=filter_criteria) |
                Q(description__icontains=filter_criteria)
        )
        weather_stations = self.model_class.objects.all().filter(filter_condition)
        serializer = self.serializer_class(weather_stations, many=True)
        return Response(serializer.data)

    # Новая метеостанция
    # @method_permission_classes((IsAdmin, IsManager))
    @swagger_auto_schema(request_body=WeatherStationSerializer,
                         responses={200: WeatherStationSerializer()},
                         manual_parameters=[CookieParameter(), PicParameter(True)])
    def post(self, request, format=None):
        """
        Создание новой метеостанции.

        Этот метод позволяет создать новую метеостанцию, принимая данные в формате JSON через тело запроса.
        В случае успешного создания возвращается информация о созданной метеостанции.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            weather_station = serializer.save()
            pic = request.FILES.get("pic")
            pic_result = add_pic(weather_station, pic)
            if 'error' in pic_result.data:
                return pic_result
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WeatherStationDetail(APIView):
    model_class = WeatherStation
    serializer_class = WeatherStationSerializer
    parser_classes = (MultiPartParser, FormParser)

    # Вернуть информацию о станции
    @swagger_auto_schema(responses={200: WeatherStationSerializer()})
    #@authentication_classes([])
    #@method_permission_classes((AllowAny,))
    def get(self, request, pk, format=None):
        """
        Получение информации о метеостанции.

        Этот метод возвращает информацию о метеостанции по указанному идентификатору.
        """
        weather_station = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(weather_station)
        return Response(serializer.data)

    # Обновить инфорацию о станции
    @swagger_auto_schema(request_body=WeatherStationSerializer,
                         responses={200: WeatherStationSerializer()},
                         manual_parameters=[CookieParameter(), PicParameter(False)])
    #@method_permission_classes((IsAdmin, IsManager,))
    def put(self, request, pk, format=None):
        """
        Обновление информации о метеостанции.

        Этот метод позволяет обновить информацию о метеостанции, принимая новые данные в формате JSON через тело запроса.
        В случае успешного обновления возвращается обновленная информация о метеостанции.
        """
        weather_station = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(weather_station, data=request.data, partial=True)
        if 'pic' in serializer.initial_data:
            pic_result = add_pic(weather_station, serializer.initial_data['pic'])
            if 'error' in pic_result.data:
                return pic_result
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удалить информацию о станции
    @swagger_auto_schema(responses={204: "Success"},
                         manual_parameters=[CookieParameter()])
    #@method_permission_classes((IsAdmin,))
    def delete(self, request, pk, format=None):
        """
        Удаление информации о метеостанции.

        Этот метод удаляет информацию о метеостанции по указанному идентификатору.
        """
        weather_station = get_object_or_404(self.model_class, pk=pk)
        weather_station.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeasurementsList(APIView):
    model_class = Measurement
    serializer_class = MeasurementSerializer

    # Список измерений
    @swagger_auto_schema(responses={200: MeasurementSerializer(many=True)},
                         manual_parameters=[CookieParameter()])
    #@method_permission_classes((ManagerOrMeteo,))
    def get(self, request, format=None):
        """
        Получение списка измерений.

        Этот метод возвращает список измерений.
        """
        measurements = self.model_class.objects.all()
        serializer = self.serializer_class(measurements, many=True)
        return Response(serializer.data)

    # Новое измерение
    @swagger_auto_schema(request_body=UploadMeasurementSerializer,
                         responses={201: MeasurementSerializer()},
                         manual_parameters=[CookieParameter()])
    #@method_permission_classes((ManagerOrMeteo,))
    def post(self, request, format=None):
        """
        Создание нового измерения.

        Этот метод позволяет создать новое измерение, принимая данные в формате JSON через тело запроса.
        В случае успешного создания возвращается информация о новом измерении.
        """
        session_id = request.COOKIES.get("session_id")
        session = session_storage.get(session_id)
        user = WeStatsUser.objects.get(email=session.decode('utf-8'))
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['creator'] = user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeasurementsDetail(APIView):
    model_class = Measurement
    serializer_class = MeasurementSerializer

    # Вернуть измерение
    @swagger_auto_schema(responses={200: MeasurementSerializer()},
                         manual_parameters=[CookieParameter()])
    @method_permission_classes((ManagerOrMeteo,))
    def get(self, request, pk, format=None):
        """
        Получение информации об измерении.

        Этот метод возвращает информацию о конкретном измерении по его идентификатору.
        """
        measurement = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(measurement)
        return Response(serializer.data)

    # Обновить измерения
    @swagger_auto_schema(request_body=UploadMeasurementSerializer,
                         responses={200: MeasurementSerializer()},
                         manual_parameters=[CookieParameter()])
    @method_permission_classes((ManagerOrMeteo,))
    def put(self, request, pk, format=None):
        """
        Обновление информации об измерении.

        Этот метод позволяет обновить информацию о конкретном измерении, принимая новые данные в формате JSON через тело запроса.
        В случае успешного обновления возвращается обновленная информация об измерении.
        """
        measurement = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(measurement, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удалить измерение
    @swagger_auto_schema(responses={204: "Success"},
                         manual_parameters=[CookieParameter()])
    @method_permission_classes((ManagerOrMeteo,))
    def delete(self, request, pk, format=None):
        """
        Удаление измерения.

        Этот метод удаляет конкретное измерение по его идентификатору.
        """
        measurement = get_object_or_404(self.model_class, pk=pk)
        measurement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderInfoList(APIView):
    model_class = OrderInfo
    serializer_class = OrderInfoSerializer

    # Список заказов на снятие показаний станции
    #@method_permission_classes((IsManager,))
    @swagger_auto_schema(responses={200: OrderInfoSerializer(many=True)},
                         manual_parameters=[CookieParameter()])
    def get(self, request, format=None):
        """
        Получение списка заказов на снятие показаний станции.

        Этот метод возвращает список всех заказов на снятие показаний станции.
        """
        orders = self.model_class.objects.all()
        serializer = self.serializer_class(orders, many=True)
        return Response(serializer.data)

    # Новый заказ на снятие показаний станции
    # @method_permission_classes((AllowAny,))
    @swagger_auto_schema(responses={201: OrderInfoSerializer(), 400: "Bad Request"},
                         manual_parameters=[CookieParameter()])
    def post(self, request, format=None):
        """
        Создание нового заказа на снятие показаний станции.

        Этот метод позволяет создать новый заказ на снятие показаний станции, принимая данные в формате JSON через тело запроса.
        Создатель заказа устанавливается по session_id.
        В случае успешного создания возвращается информация о созданном заказе.
        """
        session_id = request.COOKIES.get("session_id")
        session = session_storage.get(session_id)
        user = WeStatsUser.objects.get(email=session.decode('utf-8'))
        existing_draft_order = OrderInfo.objects.filter(creator=user, status='draft').first()
        if existing_draft_order:
            return Response({'detail': 'You already have an existing draft order.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderUserList(APIView):
    model_class = OrderInfo
    serializer_class = TotalOrderInfoSerializer

    @swagger_auto_schema(responses={200: TotalOrderInfoSerializer(many=True)},
                         manual_parameters=[CookieParameter()])
    def get(self, request):
        """
        Получение списка заказов пользователя.

        Этот метод возвращает список всех заказов пользователя, исключая заказы со статусом "черновик".
        """
        session_id = request.COOKIES.get("session_id")
        session = session_storage.get(session_id)
        user = WeStatsUser.objects.get(email=session.decode('utf-8'))

        orders = self.model_class.objects.filter(creator=user).exclude(status__exact='draft')
        serializer = self.serializer_class(orders, many=True)

        response_data = []
        for order in orders:
            measurement_ids = OrderItemMeasurement.objects.filter(order=order).values_list('measurement', flat=True)
            measurements = Measurement.objects.filter(measurement_id__in=measurement_ids)

            total_order_info = TotalOrderInfo(order=order, measurements=measurements)
            serializer = TotalOrderInfoSerializer(total_order_info)
            response_data.append(serializer.data)

        return Response(response_data, status=status.HTTP_200_OK)


class OrderUserCurrent(APIView):
    model_class = OrderInfo
    serializer_class = TotalOrderInfoSerializer

    @swagger_auto_schema(responses={200: TotalOrderInfoSerializer()},
                         manual_parameters=[CookieParameter()])
    def get(self, request):
        """
        Получение текущего заказа пользователя.

        Этот метод возвращает информацию о текущем заказе пользователя со статусом "черновик",
        включая связанные с ним измерения, если такой заказ существует.
        """
        session_id = request.COOKIES.get("session_id")
        session = session_storage.get(session_id)
        user = WeStatsUser.objects.get(email=session.decode('utf-8'))
        current_order = self.model_class.objects.filter(creator=user, status='draft').first()

        if current_order:
            measurement_ids = OrderItemMeasurement.objects.filter(order=current_order).values_list('measurement', flat=True)
            measurements = Measurement.objects.filter(measurement_id__in=measurement_ids)

            total_order_info = TotalOrderInfo(order=current_order, measurements=measurements)
            serializer = TotalOrderInfoSerializer(total_order_info)

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(None, status=status.HTTP_200_OK)


class OrderDetail(APIView):
    @swagger_auto_schema(responses={200: TotalOrderInfoSerializer(), 403: "Нет прав на просмотр заказа"},
                         manual_parameters=[CookieParameter()])
    def get(self, request, pk, *args, **kwargs):
        """
        Получение информации о заказе.

        Этот метод возвращает информацию о заказе с указанным идентификатором, включая связанные с ним измерения.
        Доступен только для владельцев заказа и пользователей-модераторов.
        """
        session_id = request.COOKIES.get("session_id")
        session = session_storage.get(session_id)
        user = WeStatsUser.objects.get(email=session.decode('utf-8'))
        order = get_object_or_404(OrderInfo, order_id=pk)
        if not (user.user_role in ['r_admin', 'r_manager']) and order.creator != user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        measurement_ids = OrderItemMeasurement.objects.filter(order=order).values_list('measurement', flat=True)
        measurements = Measurement.objects.filter(measurement_id__in=measurement_ids)

        # Создать экземпляр TotalOrderInfo
        total_order_info = TotalOrderInfo(order=order, measurements=measurements)
        serializer = TotalOrderInfoSerializer(total_order_info)

        return Response(serializer.data, status=status.HTTP_200_OK)


ASYNC_HOST = 'http://localhost:8080'


class OrderFormat(APIView):
    @swagger_auto_schema(responses={200: OrderInfoSerializer()},
                         manual_parameters=[CookieParameter()])
    def patch(self, request, pk):
        """
        Формирование заказа.

        Этот метод отправляет запрос на оплату и формирование заказа.
        Если успешно, обновляет информацию о заказе и возвращает его.
        """
        order = get_object_or_404(OrderInfo, order_id=pk)
        try:
            capture_url = ASYNC_HOST + '/capture'
            response = requests.get(capture_url)
            if response.status_code == 200:
                order.formation_date = timezone.now()
                order.status = 'formed'
                order.save()
                serializer = OrderInfoSerializer(order)
                return Response(serializer.data)
            else:
                return Response({'error': 'Failed to capture data'}, status=response.status_code)
        except requests.exceptions.ConnectionError:
            return Response({'error': 'Failed to connect to capture server'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderDelete(APIView):
    @swagger_auto_schema(responses={200: OrderInfoSerializer()},
                         manual_parameters=[CookieParameter()])
    def patch(self, request, pk):
        """
        Удаление заказа.

        Этот метод отправляет запрос на удаление заказа. Если успешно, обновляет информацию о заказе и возвращает его.
        """
        order = get_object_or_404(OrderInfo, order_id=pk)
        order.formation_date = timezone.now()
        order.status = 'deleted'
        order.save()
        serializer = OrderInfoSerializer(order)
        return Response(serializer.data)


class OrderAccept(APIView):
    @swagger_auto_schema(responses={200: OrderInfoSerializer()},
                         manual_parameters=[CookieParameter()])
    def patch(self, request, pk):
        """
        Подтверждение заказа.

        Этот метод отправляет запрос на подтверждение заказа. Если успешно, обновляет информацию о заказе и возвращает его.
        """
        order = get_object_or_404(OrderInfo, order_id=pk)
        try:
            capture_url = ASYNC_HOST + '/debit'
            response = requests.get(capture_url)
            if response.status_code == 200:
                order.completion_date = timezone.now()
                order.status = 'completed'
                order.save()
                serializer = OrderInfoSerializer(order)
                return Response(serializer.data)
            else:
                return Response({'error': 'Failed to capture data'}, status=response.status_code)
        except requests.exceptions.ConnectionError:
            return Response({'error': 'Failed to connect to capture server'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderReject(APIView):
    @swagger_auto_schema(responses={200: OrderInfoSerializer()},
                         manual_parameters=[CookieParameter()])
    def patch(self, request, pk):
        """
        Отклонение заказа.

        Этот метод отправляет запрос на отклонение заказа. Если успешно, обновляет информацию о заказе и возвращает его.
        """
        order = get_object_or_404(OrderInfo, order_id=pk)
        try:
            capture_url = ASYNC_HOST + '/credit'
            response = requests.get(capture_url)
            if response.status_code == 200:
                order.completion_date = timezone.now()
                order.status = 'rejected'
                order.save()
                serializer = OrderInfoSerializer(order)
                return Response(serializer.data)
            else:
                return Response({'error': 'Failed to capture data'}, status=response.status_code)
        except requests.exceptions.ConnectionError:
            return Response({'error': 'Failed to connect to capture server'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddOrderItem(APIView):
    @swagger_auto_schema(request_body=OrderAddItemSerializer,
                         responses={200: OrderItemMeasurementSerializer()},
                         manual_parameters=[CookieParameter()])
    def post(self, request, pk):
        """
        Добавление измерения к заказу.

        Этот метод добавляет измерение к заказу. Возвращает информацию о добавленном измерении.
        """
        # Получаем объект заказа по order_id
        try:
            order = OrderInfo.objects.get(order_id=pk)
        except OrderInfo.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        measurement_id = request.data.get('measurement_id')
        # Получаем объект измерения по measurement_id
        try:
            measurement = Measurement.objects.get(measurement_id=measurement_id)
        except Measurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=status.HTTP_404_NOT_FOUND)

        # Создаем и сохраняем объект OrderItemMeasurement
        order_item_measurement = OrderItemMeasurement(order=order, measurement=measurement)
        order_item_measurement.save()

        # Сериализуем созданный объект и возвращаем в ответе
        serializer = OrderItemMeasurementSerializer(order_item_measurement)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# >> OBSOLETE
'''class WeStatsUserList(APIView):
    model_class = WeStatsUser
    serializer_class = WeStatsUserSerializer

    # Список юзеров
    def get(self, request, format=None):
        users = self.model_class.objects.all()
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data)

    # Новый юзер
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WeStatsUserDetail(APIView):
    model_class = WeStatsUser
    serializer_class = WeStatsUserSerializer

    # Инфо о юзере
    def get(self, request, pk, format=None):
        user = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    # Обновить юзера
    def put(self, request, pk, format=None):
        user = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удалить юзера
    def delete(self, request, pk, format=None):
        user = get_object_or_404(self.model_class, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
        class StationsMeasurementsList(APIView):
    model_class = StationsMeasurements
    serializer_class = StationsMeasurementsSerializer

    # Список связей
    def get(self, request, format=None):
        stations_measurements = self.model_class.objects.all()
        serializer = self.serializer_class(stations_measurements, many=True)
        return Response(serializer.data)

    # Новая связь
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeasurementOrder(APIView):
    model_class = StationsMeasurements
    serializer_class = StationsMeasurementsSerializer

    # Информация о связи
    def get(self, request, pk, format=None):
        stations_measurement = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stations_measurement)
        return Response(serializer.data)

    # Обновить связь
    def put(self, request, pk, format=None):
        stations_measurement = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stations_measurement, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удалить связь
    def delete(self, request, pk, format=None):
        stations_measurement = get_object_or_404(self.model_class, pk=pk)
        stations_measurement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)'''