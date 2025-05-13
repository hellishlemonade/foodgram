from django.urls import path, include

VERSION = 'v1'

urlpatterns = [
    path('', include('api.v1.urls'))
]
