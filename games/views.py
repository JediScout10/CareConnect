from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.http import Http404
from .models import Game, GameSession, GameProgress
from django.db.models import Avg, Count, Sum

# Create your views here.

@login_required
def games_list(request):
    return render(request, 'games/games_list.html')

@login_required
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    user_progress = GameProgress.objects.filter(user=request.user, game=game).first()
    recent_sessions = GameSession.objects.filter(user=request.user, game=game)[:5]
    
    return render(request, 'games/game_detail.html', {
        'game': game,
        'user_progress': user_progress,
        'recent_sessions': recent_sessions
    })

@login_required
def play_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)  
    template_name = 'games/breathing.html' if game_id == 1 else 'games/coloring.html'
    return render(request, template_name, {'game': game})

@login_required
def complete_game(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        game_id = data.get('game_id')
        score = data.get('score')
        
        # Create a game session record
        game = get_object_or_404(Game, id=game_id)
        GameSession.objects.create(
            user=request.user,
            game=game,
            score=score,
            completed_at=timezone.now()
        )
        
        # Update user progress
        progress, created = GameProgress.objects.get_or_create(
            user=request.user,
            game=game,
            defaults={'total_score': 0, 'sessions_count': 0}
        )
        progress.total_score += score
        progress.sessions_count += 1
        progress.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def save_game_session(request):
    if request.method == 'POST':
        try:
            data = request.POST
            game = get_object_or_404(Game, id=data.get('game_id'))
            
            # Create game session
            session = GameSession.objects.create(
                user=request.user,
                game=game,
                score=int(data.get('score', 0)),
                duration=int(data.get('duration', 0)),
                completed=data.get('completed', False) == 'true'
            )
            
            # Update or create game progress
            progress, created = GameProgress.objects.get_or_create(
                user=request.user,
                game=game,
                defaults={
                    'high_score': session.score,
                    'total_sessions': 1,
                    'total_duration': session.duration
                }
            )
            
            if not created:
                if session.score > progress.high_score:
                    progress.high_score = session.score
                progress.total_sessions += 1
                progress.total_duration += session.duration
                progress.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def game_stats(request):
    user_progress = GameProgress.objects.filter(user=request.user)
    recent_sessions = GameSession.objects.filter(user=request.user).order_by('-played_at')[:10]
    
    stats = {
        'total_games_played': user_progress.aggregate(total=Count('id'))['total'],
        'total_duration': user_progress.aggregate(total=Sum('total_duration'))['total'],
        'average_score': user_progress.aggregate(avg=Avg('high_score'))['avg'],
        'recent_sessions': list(recent_sessions.values('game__name', 'score', 'duration', 'played_at'))
    }
    
    return JsonResponse(stats)

@login_required
def save_drawing(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            image_data = data.get('image')
            
            # Here you would typically save the drawing data
            # For now, we'll just return success
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'}, status=400)
