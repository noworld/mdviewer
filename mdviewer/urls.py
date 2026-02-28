from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('library.api_urls')),
    path('', include('library.urls')),
]
