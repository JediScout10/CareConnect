# meditation\urls.py
from django.urls import path
from . import views

app_name = 'meditation'

urlpatterns = [
    path('', views.meditation_page, name='meditation_page'),
    path('save-session/', views.save_session, name='save_session'),
]
