from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.http import JsonResponse

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mental-health-test/', views.mental_health_test, name='mental_health_test'),
    path('test-history/', views.test_history, name='test_history'),
    path('test-detail/<int:pk>/', views.test_detail, name='test_detail'),
    path('mood-tracking/', views.mood_tracking, name='mood_tracking'),
    path('mood-history/', views.mood_history, name='mood_history'),
    path('report/', views.report, name='report'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    # Chatbot and resource routes
    path('chatbot/', views.chatbot, name='chatbot'),
    path('resource-click/<int:resource_id>/', views.resource_click, name='resource_click'),
    path('end-chat-session/', views.end_chat_session, name='end_chat_session'),
]