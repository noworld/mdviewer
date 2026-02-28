from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='library/search.html')),
    path('search/', TemplateView.as_view(template_name='library/search.html')),
    path('upload/', TemplateView.as_view(template_name='library/upload.html')),
    path('admin-panel/', TemplateView.as_view(template_name='library/admin.html')),
]
