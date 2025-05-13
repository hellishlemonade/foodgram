from django.urls import path, include

VERSION = 'v1'

urlpatterns = [
    path(f'{VERSION}/', include('api.v1.urls'))
]
