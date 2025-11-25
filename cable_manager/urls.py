from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-cable/', views.add_cable_line, name='add_cable_line'),
    path('add-measurement/', views.add_measurement_session, name='add_measurement_session'),
    path('add-test/', views.add_high_voltage_test, name='add_high_voltage_test'),
    path('cable/<int:cable_id>/', views.cable_line_detail, name='cable_line_detail'),
    path('ai-analysis/', views.ai_analysis, name='ai_analysis'),  # НОВЫЙ МАРШРУТ
    path('train-ai/', views.train_ai_model, name='train_ai_model'),  # НОВЫЙ МАРШРУТ
    path('statistics/', views.statistics, name='statistics'),
]