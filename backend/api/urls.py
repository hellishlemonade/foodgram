from django.urls import include, path

VERSION = 'v1'

urlpatterns = [
    path('', include('api.v1.urls'))
]
