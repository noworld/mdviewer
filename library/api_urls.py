from django.urls import path
from library import views

urlpatterns = [
    path('library/', views.LibraryListCreateView.as_view()),
    path('library/stats/', views.LibraryStatsView.as_view()),
    path('library/clear/', views.LibraryClearView.as_view()),
    path('library/<int:pk>/', views.LibraryDetailView.as_view()),
]
