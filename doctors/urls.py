from django.urls import path
from . import views

urlpatterns = [
    path('doctor/dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('doctor/appointment/<int:appointment_id>/status/', views.update_appointment_status_view, name='update_appointment_status'),
    path('doctor/slots/generate/', views.generate_slots_view, name='generate_slots'),
    path('doctor/profile/edit/', views.doctor_profile_edit_view, name='doctor_profile_edit'),
]
