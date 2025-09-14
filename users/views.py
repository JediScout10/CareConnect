from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomLoginForm, MoodEntryForm, MentalHealthTestForm, PHQ9Form, GAD7Form, PSS10Form
from .models import CustomUser, MentalHealthTest, MoodEntry, ActionPlan, TestRecommendation, ChatSession, ChatMessage, Resource, ResourceClick
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth

def landpage_view(request):
    """View for the landing page"""
    return render(request, 'users/landpage.html')

def mental_health_test(request):
    """View for mental health test with multiple assessment types"""
    test_type = request.GET.get('test_type')
    test_form = None
    test_type_display = ''
    
    # Handle form submission
    if request.method == 'POST':
        test_type = request.POST.get('test_type')
        
        if test_type == 'PHQ-9':
            form = PHQ9Form(request.POST)
            test_type_display = 'PHQ-9 (Depression Screening)'
        elif test_type == 'GAD-7':
            form = GAD7Form(request.POST)
            test_type_display = 'GAD-7 (Anxiety Screening)'
        elif test_type == 'PSS':
            form = PSS10Form(request.POST)
            test_type_display = 'PSS-10 (Perceived Stress Scale)'
        else:
            # Invalid test type
            return redirect('users:mental_health_test')
        
        if form.is_valid():
            # Calculate score
            score = form.calculate_score()
            
            # Create new MentalHealthTest object
            test = MentalHealthTest(
                user=request.user,
                test_type=test_type,
                score=score
            )
            test.save()
            
            # Redirect to test history page
            return redirect('users:test_history')
    
    # Display form based on selected test type
    elif test_type:
        if test_type == 'PHQ-9':
            test_form = PHQ9Form()
            test_type_display = 'PHQ-9 (Depression Screening)'
        elif test_type == 'GAD-7':
            test_form = GAD7Form()
            test_type_display = 'GAD-7 (Anxiety Screening)'
        elif test_type == 'PSS':
            test_form = PSS10Form()
            test_type_display = 'PSS-10 (Perceived Stress Scale)'
    
    return render(request, 'users/mental_health_test.html', {
        'test_form': test_form,
        'test_type': test_type,
        'test_type_display': test_type_display
    })

def login_view(request):
    """Custom login view that handles email authentication"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('users:dashboard')
        else:
            return render(request, 'users/login.html', {'error': 'Invalid email or password.'})
    
    return render(request, 'users/login.html')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard view"""
    return render(request, 'users/dashboard.html')

@login_required
def test_history(request):
    """View for displaying mental health test history"""
    tests = MentalHealthTest.objects.filter(user=request.user).order_by('-date_taken')
    total_tests = tests.count()
    
    # Count tests by type
    phq9_tests = tests.filter(test_type='PHQ-9').count()
    gad7_tests = tests.filter(test_type='GAD-7').count()
    pss_tests = tests.filter(test_type='PSS').count()
    
    return render(request, 'users/test_history.html', {
        'tests': tests,
        'total_tests': total_tests,
        'phq9_tests': phq9_tests,
        'gad7_tests': gad7_tests,
        'pss_tests': pss_tests
    })

@staff_member_required
def admin_analytics(request):
    # Get all tests
    all_tests = MentalHealthTest.objects.all()
    
    # Count tests by type
    total_tests = all_tests.count()
    phq9_count = all_tests.filter(test_type='PHQ-9').count()
    gad7_count = all_tests.filter(test_type='GAD-7').count()
    pss_count = all_tests.filter(test_type='PSS').count()
    
    # Calculate average scores
    phq9_avg = all_tests.filter(test_type='PHQ-9').aggregate(Avg('score'))['score__avg'] or 0
    gad7_avg = all_tests.filter(test_type='GAD-7').aggregate(Avg('score'))['score__avg'] or 0
    pss_avg = all_tests.filter(test_type='PSS').aggregate(Avg('score'))['score__avg'] or 0
    
    # User statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(mentalhealthtest__isnull=False).distinct().count()
    tests_per_user = total_tests / total_users if total_users > 0 else 0
    
    # Tests over time (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    tests_by_day = all_tests.filter(date_taken__gte=thirty_days_ago)\
                          .annotate(date=TruncDate('date_taken'))\
                          .values('date')\
                          .annotate(count=Count('id'))\
                          .order_by('date')
    
    # Prepare data for time series chart
    dates = []
    counts = []
    
    # Create a complete date range for the last 30 days
    current_date = thirty_days_ago.date()
    end_date = timezone.now().date()
    date_dict = {}
    
    while current_date <= end_date:
        date_dict[current_date.isoformat()] = 0
        current_date += timedelta(days=1)
    
    # Fill in actual counts
    for entry in tests_by_day:
        date_str = entry['date'].isoformat()
        date_dict[date_str] = entry['count']
    
    # Convert to lists for the chart
    for date_str, count in date_dict.items():
        dates.append(date_str)
        counts.append(count)
    
    context = {
        'total_tests': total_tests,
        'phq9_count': phq9_count,
        'gad7_count': gad7_count,
        'pss_count': pss_count,
        'phq9_avg': phq9_avg,
        'gad7_avg': gad7_avg,
        'pss_avg': pss_avg,
        'total_users': total_users,
        'active_users': active_users,
        'tests_per_user': tests_per_user,
        'time_labels': json.dumps(dates),
        'time_data': json.dumps(counts),
    }
    
    return render(request, 'users/admin_analytics.html', context)

@login_required
def mood_tracking(request):
    """View for mood tracking functionality"""
    if request.method == 'POST':
        form = MoodEntryForm(request.POST)
        if form.is_valid():
            mood_entry = form.save(commit=False)
            mood_entry.user = request.user
            mood_entry.save()
            return redirect('users:mood_tracking')
    else:
        form = MoodEntryForm()
    
    # Get user's mood entries
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')
    
    return render(request, 'users/mood_tracking.html', {
        'form': form,
        'mood_entries': mood_entries
    })

@login_required
def report(request):
    """View for generating reports based on user data"""
    # Get user's mental health tests
    tests = MentalHealthTest.objects.filter(user=request.user).order_by('-date_taken')
    
    # Get user's mood entries
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')
    
    return render(request, 'users/report.html', {
        'tests': tests,
        'mood_entries': mood_entries
    })

@login_required
def test_detail(request, pk):
    """View for displaying details of a specific mental health test"""
    test = get_object_or_404(MentalHealthTest, pk=pk, user=request.user)
    
    # Get or create recommendation
    recommendation, created = TestRecommendation.objects.get_or_create(
        test=test,
        defaults={
            'severity': test.get_severity(),
            'recommendation_type': test.get_recommendation_type()
        }
    )
    
    # Handle recommendation acceptance
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept' and recommendation:
            recommendation.accepted = True
            recommendation.save()
            
            # Redirect based on recommendation type
            if recommendation.recommendation_type == 'chatbot':
                return redirect('users:chatbot')
            elif recommendation.recommendation_type == 'counselor':
                messages.success(request, 'Please contact a counselor or mental health professional.')
                return redirect('users:dashboard')
            else:
                # For self-care, stay on the page
                pass
        elif action == 'decline' and recommendation:
            recommendation.accepted = False
            recommendation.save()
            messages.info(request, 'You can always access these recommendations later.')
    
    # Determine which template to use based on test type
    if test.test_type == 'PHQ-9':
        template = 'users/test_detail_phq9.html'
    elif test.test_type == 'GAD-7':
        template = 'users/test_detail_gad7.html'
    elif test.test_type == 'PSS':
        template = 'users/test_detail_pss.html'
    else:
        template = 'users/test_detail.html'
    
    return render(request, template, {
        'test': test,
        'recommendation': recommendation
    })

@login_required
def chatbot(request):
    """View for AI-guided chatbot support"""
    # Get or create a chat session
    active_session = ChatSession.objects.filter(user=request.user, ended_at__isnull=True).first()
    
    if not active_session:
        active_session = ChatSession.objects.create(user=request.user)
    
    # Handle message submission
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            # Save user message
            ChatMessage.objects.create(
                session=active_session,
                message_type='user',
                content=message_content
            )
            
            # Generate AI response based on user message
            response = generate_chatbot_response(message_content, active_session)
            
            # Save system message
            ChatMessage.objects.create(
                session=active_session,
                message_type='system',
                content=response['message']
            )
            
            # If resources were suggested, track them
            if 'resources' in response and response['resources']:
                for resource_id in response['resources']:
                    try:
                        resource = Resource.objects.get(id=resource_id)
                        # We don't create ResourceClick here, only when user actually clicks
                    except Resource.DoesNotExist:
                        pass
    
    # Get chat history for this session
    messages = active_session.messages.all()
    
    # Get relevant resources to display
    resources = Resource.objects.filter(is_active=True)[:5]  # Limit to 5 resources initially
    
    return render(request, 'users/chatbot.html', {
        'session': active_session,
        'messages': messages,
        'resources': resources
    })

@login_required
def resource_click(request, resource_id):
    """Track when a user clicks on a resource"""
    if request.method == 'POST':
        resource = get_object_or_404(Resource, id=resource_id)
        active_session = ChatSession.objects.filter(user=request.user, ended_at__isnull=True).first()
        
        # Record the click
        ResourceClick.objects.create(
            user=request.user,
            resource=resource,
            chat_session=active_session
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def end_chat_session(request):
    """End the current chat session"""
    if request.method == 'POST':
        active_session = ChatSession.objects.filter(user=request.user, ended_at__isnull=True).first()
        if active_session:
            active_session.ended_at = timezone.now()
            active_session.save()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

def generate_chatbot_response(message, session):
    """Generate a response from the chatbot based on user message"""
    # Check for high distress keywords
    high_distress_keywords = ['suicide', 'kill myself', 'end my life', 'want to die', 'harming myself']
    is_high_distress = any(keyword in message.lower() for keyword in high_distress_keywords)
    
    # Basic response templates
    if is_high_distress:
        return {
            'message': "I'm concerned about what you've shared. It's important that you speak with a mental health professional right away. Would you like me to provide you with crisis resources or help you book an appointment with a counselor?",
            'resources': Resource.objects.filter(resource_type='helpline').values_list('id', flat=True)
        }
    
    # Check for specific help requests
    if 'breathing' in message.lower() or 'anxious' in message.lower() or 'anxiety' in message.lower():
        return {
            'message': "Breathing exercises can help reduce anxiety. Try this: Breathe in slowly through your nose for 4 counts, hold for 7 counts, then exhale through your mouth for 8 counts. Repeat this 4-7-8 breathing pattern 4 times.",
            'resources': Resource.objects.filter(resource_type='breathing').values_list('id', flat=True)
        }
    
    if 'journal' in message.lower() or 'writing' in message.lower() or 'express' in message.lower():
        return {
            'message': "Journaling can be a great way to process your thoughts and feelings. Here's a prompt to get you started: Write about a challenge you're facing right now and three possible ways you might address it.",
            'resources': Resource.objects.filter(resource_type='journaling').values_list('id', flat=True)
        }
    
    if 'stress' in message.lower() or 'overwhelm' in message.lower() or 'pressure' in message.lower():
        return {
            'message': "It sounds like you're feeling stressed. One technique that might help is to break down what's overwhelming you into smaller, manageable tasks. You might also try a brief mindfulness exercise: focus on your surroundings and name 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste.",
            'resources': Resource.objects.filter(resource_type='stress_management').values_list('id', flat=True)
        }
    
    # Default response
    return {
        'message': "I'm here to support you. Would you like to try a breathing exercise, get a journaling prompt, or learn about stress management techniques? You can also tell me more about what's on your mind.",
        'resources': []
    }

@login_required
def mood_history(request):
    """View for displaying mood history"""
    # Get user's mood entries
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')
    
    return render(request, 'users/mood_history.html', {
        'mood_entries': mood_entries
    })