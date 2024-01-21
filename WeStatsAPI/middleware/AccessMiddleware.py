from django.http import HttpResponseForbidden
from WeStatsAPI.models import WeStatsUser

from django.conf import settings
import redis
import re


EXCLUDED_PATHS = {
    '/login': ['ANY'],
    '/stations': ['GET'],
    re.compile(r'^/stations/\d+'): ['GET'],
    re.compile(r'^/users/\d+'): ['GET'],
    re.compile(r'^/orders/\d+'): ['GET'],
    re.compile(r'^/measurements/\d+'): ['GET'],
    '/swagger/': ['ANY'],
    '/measurements': ['GET', 'POST'],
}


ROLES_PERMISSIONS = {
    'just_user': {
        '/orders': ['GET', 'POST'],
        re.compile(r'^/orders/\d+/format'): ['PATCH'],
        re.compile(r'^/orders/\d+/delete'): ['PATCH'],
        re.compile(r'^/orders/\d+/addItem'): ['POST'],
    },
    'meteorologist': {
        '/measurements': ['GET', 'POST'],
        re.compile(r'^/measurements/\d+'): ['GET'],
    },
    'r_manager': {
        '/measurements': ['GET', 'POST'],
        re.compile(r'^/measurements/\d+'): ['ANY'],
        '/orders': ['GET', 'POST'],
        re.compile(r'^/orders/\d+'): ['GET'],
        re.compile(r'^/orders/\d+/accept'): ['PATCH'],
        re.compile(r'^/orders/\d+/reject'): ['PATCH'],
    },
    'r_admin': {
        '/stations': ['ANY'],
        re.compile(r'^/stations/\d+'): ['ANY'],
        '/measurements': ['GET', 'POST'],
        re.compile(r'^/measurements/\d+'): ['ANY'],
        '/users': ['ANY'],

        '/orders': ['ANY'],
        re.compile(r'^/orders/\d+'): ['ANY'],
        re.compile(r'^/orders/\d+/format'): ['PATCH'],
        re.compile(r'^/orders/\d+/delete'): ['PATCH'],
        re.compile(r'^/orders/\d+/addItem'): ['PATCH'],
        re.compile(r'^/orders/\d+/accept'): ['PATCH'],
        re.compile(r'^/orders/\d+/reject'): ['PATCH'],
        re.compile(r'^/update_user_role/\d+'): ['ANY'],
    },
}
COMMON_PERMISSIONS = {
    '/logout': ['ANY'],
    '/profile': ['GET'],
    '/userorders': ['GET'],
    '/userorders/current': ['GET'],
}


# Redis
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class AccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            for path, methods in EXCLUDED_PATHS.items():
                if isinstance(path, str):
                    # Если путь строковый, то проверяем точное соответствие
                    #print(path, methods, '/', request.path, request.method)
                    if request.path == path:
                        print('TRYING', path, methods)
                        if 'ANY' in methods or request.method in methods:
                            print('k')
                            return self.get_response(request)
                elif isinstance(path, re.Pattern):
                    #print(path, methods, '/', request.path, request.method)
                    if path.match(request.path):
                        if 'ANY' in methods or request.method in methods:
                            return self.get_response(request)

            # Идентификатор сессии из куки запроса
            session_id = request.COOKIES.get("session_id")
            #print(session_id)
            if session_id:
                try:
                    # Попытка получения данных из Redis
                    session = session_storage.get(session_id)
                    if session:
                        user = WeStatsUser.objects.get(email=session.decode('utf-8'))

                        if self.has_access(user, request.path, request.method):
                            return self.get_response(request)
                        else:
                            return HttpResponseForbidden("REDIS. Access denied.")
                    else:
                        return HttpResponseForbidden("Session data not found in Redis.")
                except Exception as e:
                    return HttpResponseForbidden(f"Error checking Redis session: {str(e)}")
            else:
                return HttpResponseForbidden("Session ID not found in cookies.")

        except Exception as er:
            print(er)

    def has_access(self, user, requested_path, request_method):
        try:
            for path, methods in COMMON_PERMISSIONS.items():
                if isinstance(path, str):
                    if requested_path == path:
                        if 'ANY' in methods or request_method in methods:
                            return True
                elif isinstance(path, re.Pattern):
                    if path.match(requested_path):
                        if 'ANY' in methods or request_method in methods:
                            return True

            perms = ROLES_PERMISSIONS[user.user_role]
            for path, methods in perms.items():
                if isinstance(path, str):
                    #print(path, methods, '/', requested_path, request_method)
                    if requested_path == path:
                        print(requested_path, path)
                        print(request_method in methods)
                        if 'ANY' in methods or request_method in methods:
                            return True
                elif isinstance(path, re.Pattern):
                    #print(path, methods, '/', requested_path, request_method)
                    if path.match(requested_path):
                        if 'ANY' in methods or request_method in methods:
                            return True

            print('REDIS Forbidden')
            return False

        except WeStatsUser.DoesNotExist:
            pass

        return False
