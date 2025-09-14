from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.games_list, name='games_list'),
    path('<int:game_id>/play/', views.play_game, name='play_game'),
    path('complete/', views.complete_game, name='complete_game'),
    path('save-drawing/', views.save_drawing, name='save_drawing'),
] 