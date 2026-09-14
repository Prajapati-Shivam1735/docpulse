from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('search/', views.search_view, name='search'),
    path('book/<int:doctor_id>/', views.book_appointment_view, name='book_appointment'),
    path('appointment/<str:booking_reference>/slip/', views.appointment_slip_view, name='appointment_slip'),
    path('track/', views.track_appointment_view, name='track_appointment'),
]
