from django.urls import path
from . import views

urlpatterns = [
    path('patient/register/', views.patient_register_view, name='patient_register'),
    path('patient/login/', views.patient_login_view, name='patient_login'),
    path('doctor/register/', views.doctor_register_view, name='doctor_register'),
    path('doctor/login/', views.doctor_login_view, name='doctor_login'),
    path('logout/', views.logout_view, name='logout'),
]
