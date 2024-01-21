from drf_yasg import openapi


# Параметр куки сессии
class CookieParameter(openapi.Parameter):
    def __init__(self):
        super().__init__(
            name='session_id',
            in_='cookie',
            type=openapi.TYPE_STRING,
            description='Куки сессии',
            required=True
        )


# Параметр новой роли
class RoleParameter(openapi.Parameter):
    def __init__(self):
        super().__init__(
            name='role',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            description='Новая роль пользователя',
            required=True
        )


# Параметр upload-image
class PicParameter(openapi.Parameter):
    def __init__(self, required):
        super().__init__(
            name='pic',
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description='Изображение для загрузки',
            required=required
        )


# Параметр фильтрации
class FilterParameter(openapi.Parameter):
    def __init__(self):
        super().__init__(
            name='filter',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            description='Ключевое слово для поиска вхождений',
            required=False
        )