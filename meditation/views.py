# meditation\views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import MeditationSession
from django.db.models import Sum
import json

@login_required
def meditation_page(request):
    # Get user's meditation statistics
    total_meditation = MeditationSession.objects.filter(user=request.user).aggregate(total=Sum('duration'))['total'] or 0
    total_sessions = MeditationSession.objects.filter(user=request.user).count()
    
    # Calculate meditation streak
    today = timezone.now().date()
    streak = 0
    current_date = today
    
    while MeditationSession.objects.filter(user=request.user, created_at__date=current_date).exists():
        streak += 1
        current_date -= timedelta(days=1)
    
    # Get recent sessions
    recent_sessions = MeditationSession.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'total_meditation': total_meditation,
        'total_sessions': total_sessions,
        'meditation_streak': streak,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'meditation/meditation_page.html', context)

@login_required
@require_POST
def save_session(request):
    try:
        data = json.loads(request.body)
        duration = data.get('duration')
        
        if not duration:
            return JsonResponse({'status': 'error', 'message': 'Duration is required'}, status=400)
        
        now = timezone.now()
        session = MeditationSession.objects.create(
            user=request.user,
            duration=duration,
            date=now.date(),
            created_at=now
        )
        
        # Return more detailed response for debugging
        return JsonResponse({
            'status': 'success',
            'session': {
                'id': session.id,
                'duration': session.duration,
                'date': session.date.strftime('%Y-%m-%d'),
                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e),
            'type': str(type(e))
        }, status=500)

@login_required
def start_meditation(request):
    return render(request, "meditation/start.html")


