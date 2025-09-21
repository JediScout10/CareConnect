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
    """View for mental health test selection and taking"""
    test_type = request.GET.get('test_type')
    
    # If no test type specified, show test selection page
    if not test_type:
        return render(request, 'users/mental_health_test.html')
    
    # Handle form submission
    if request.method == 'POST':
        # Get test_type from POST data if not in GET
        if not test_type:
            test_type = request.POST.get('test_type')
            
        if test_type == 'PHQ-9':
            form = PHQ9Form(request.POST)
        elif test_type == 'GAD-7':
            form = GAD7Form(request.POST)
        elif test_type == 'PSS-10':
            form = PSS10Form(request.POST)
        else:
            messages.error(request, 'Invalid test type selected.')
            return redirect('users:mental_health_test')
        
        if form.is_valid():
            try:
                score = form.calculate_score()
                
                # For PHQ-9, capture item 9 score for caution logic
                phq9_item9_score = None
                if test_type == 'PHQ-9':
                    phq9_item9_score = int(form.cleaned_data.get('q9', 0))
                
                # Create test record
                test = MentalHealthTest.objects.create(
                    user=request.user,
                    test_type=test_type,
                    score=score,
                    phq9_item9_score=phq9_item9_score
                )
                
                messages.success(request, f'Test completed! Your {test_type} score is {score}.')
                return redirect('users:test_detail', test_id=test.id)
            except Exception as e:
                messages.error(request, f'Error processing test: {str(e)}')
                return redirect('users:mental_health_test')
        else:
            messages.error(request, 'Please answer all questions to complete the test.')
    else:
        if test_type == 'PHQ-9':
            form = PHQ9Form()
        elif test_type == 'GAD-7':
            form = GAD7Form()
        elif test_type == 'PSS-10':
            form = PSS10Form()
        else:
            messages.error(request, 'Invalid test type.')
            return redirect('users:mental_health_test')
    
    # Get test type display name
    test_type_display = {
        'PHQ-9': 'PHQ-9 (Depression Screening)',
        'GAD-7': 'GAD-7 (Anxiety Screening)', 
        'PSS-10': 'PSS-10 (Perceived Stress Scale)'
    }.get(test_type, test_type)
    
    context = {
        'test_form': form,
        'test_type': test_type,
        'test_type_display': test_type_display
    }
    
    return render(request, 'users/mental_health_test.html', context)

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
    # Get or create a chat session
    active_session = ChatSession.objects.filter(user=request.user, ended_at__isnull=True).first()
    if not active_session:
        active_session = ChatSession.objects.create(user=request.user)

    # Handle message submission
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            # Create user message
            ChatMessage.objects.create(
                session=active_session,
                message_type='user',
                content=message_content
            )
            
            # Generate and create system response
            response = generate_chatbot_response(message_content, active_session)
            ChatMessage.objects.create(
                session=active_session,
                message_type='system',
                content=response['message']
            )
            
            # Return JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': response['message'],
                    'severity': response.get('severity', 'mild')
                })
    
    # Get chat history for this session
    messages = active_session.messages.all()
    # Get relevant resources to display
    resources = Resource.objects.filter(is_active=True)[:5]
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
    """Generate dynamic chatbot response based on user message content"""
    message_lower = message.lower()
    
    # Crisis intervention - immediate response
    crisis_keywords = ['suicide', 'kill myself', 'end my life', 'want to die', 'hurt myself', 'self harm', 'better off dead']
    if any(keyword in message_lower for keyword in crisis_keywords):
        session.distress_level = 10
        session.save()
        return {
            'message': "I'm very concerned about what you've shared. Your life has value and there are people who want to help right now. Please reach out immediately:\n\n **Crisis Resources:**\n• National Suicide Prevention Lifeline: **988**\n• Crisis Text Line: Text **HOME to 741741**\n• Emergency Services: **911**\n\nYou don't have to go through this alone. Would you like me to help you find local mental health resources?",
            'severity': 'severe'
        }
    
    # Anxiety-related responses
    anxiety_keywords = ['anxious', 'panic', 'worried', 'nervous', 'scared', 'fear', 'anxiety attack', 'panic attack']
    if any(keyword in message_lower for keyword in anxiety_keywords):
        session.distress_level = 7
        session.save()
        return {
            'message': "I understand you're feeling anxious. Anxiety can be overwhelming, but there are effective ways to manage it:\n\n **Try this breathing technique:**\n• Breathe in for 4 counts\n• Hold for 4 counts\n• Breathe out for 6 counts\n• Repeat 5 times\n\n **Grounding technique (5-4-3-2-1):**\n• 5 things you can see\n• 4 things you can touch\n• 3 things you can hear\n• 2 things you can smell\n• 1 thing you can taste\n\nWould you like me to guide you through one of these techniques?",
            'severity': 'moderate'
        }
    
    # Depression-related responses
    depression_keywords = ['depressed', 'sad', 'hopeless', 'empty', 'worthless', 'tired', 'no energy', 'can\'t sleep', 'sleeping too much']
    if any(keyword in message_lower for keyword in depression_keywords):
        session.distress_level = 6
        session.save()
        return {
            'message': "I hear that you're going through a difficult time. Depression can make everything feel harder, but you're not alone in this:\n\n **Small steps that can help:**\n• Try to maintain a regular sleep schedule\n• Get some sunlight or fresh air if possible\n• Reach out to a trusted friend or family member\n• Consider gentle movement like a short walk\n• Practice self-compassion - be kind to yourself\n\n **Professional support:** If these feelings persist, talking to a mental health professional can be very helpful.\n\nWhat feels most manageable for you right now?",
            'severity': 'moderate'
        }
    
    # Stress-related responses
    stress_keywords = ['stressed', 'overwhelmed', 'pressure', 'burnout', 'exhausted', 'too much', 'can\'t cope']
    if any(keyword in message_lower for keyword in stress_keywords):
        session.distress_level = 5
        session.save()
        return {
            'message': "Stress can feel overwhelming, but there are ways to manage it effectively:\n\n⚡ **Quick stress relief:**\n• Take 5 deep breaths\n• Do a 2-minute body scan\n• Step outside for fresh air\n• Listen to calming music\n\n📝 **Longer-term strategies:**\n• Break large tasks into smaller steps\n• Set boundaries and say no when needed\n• Practice regular self-care\n• Consider time management techniques\n\nWhat's contributing most to your stress right now? Sometimes talking through it can help.",
            'severity': 'moderate'
        }
    
    # Sleep-related responses
    sleep_keywords = ['can\'t sleep', 'insomnia', 'tired', 'exhausted', 'sleep problems', 'staying awake']
    if any(keyword in message_lower for keyword in sleep_keywords):
        session.distress_level = 4
        session.save()
        return {
            'message': "Sleep problems can really affect how we feel. Here are some strategies that might help:\n\n🌙 **Sleep hygiene tips:**\n• Keep a consistent sleep schedule\n• Avoid screens 1 hour before bed\n• Create a relaxing bedtime routine\n• Keep your bedroom cool and dark\n• Avoid caffeine after 2 PM\n\n🧘 **Relaxation techniques:**\n• Progressive muscle relaxation\n• Guided meditation\n• Deep breathing exercises\n• Gentle stretching\n\nHow long have you been having trouble sleeping?",
            'severity': 'mild'
        }
    
    # Relationship/social issues
    relationship_keywords = ['lonely', 'alone', 'relationship', 'friends', 'family problems', 'isolated', 'social']
    if any(keyword in message_lower for keyword in relationship_keywords):
        session.distress_level = 4
        session.save()
        return {
            'message': "Relationships and social connections are so important for our wellbeing. It sounds like this is on your mind:\n\n🤝 **Building connections:**\n• Reach out to one person today, even briefly\n• Join activities or groups that interest you\n• Practice active listening in conversations\n• Be patient with yourself - relationships take time\n\n💭 **If you're feeling lonely:**\n• Remember that many people feel this way\n• Consider volunteering or helping others\n• Try online communities with shared interests\n• Professional counseling can help with social skills\n\nWhat kind of connection are you looking for right now?",
            'severity': 'mild'
        }
    
    # Work/school stress
    work_keywords = ['work', 'job', 'school', 'study', 'exam', 'deadline', 'boss', 'colleague', 'performance']
    if any(keyword in message_lower for keyword in work_keywords):
        session.distress_level = 4
        session.save()
        return {
            'message': "Work and school stress is very common. Let's think about some strategies:\n\n📊 **Managing workload:**\n• Prioritize tasks by importance and urgency\n• Break large projects into smaller steps\n• Take regular breaks (even 5-10 minutes helps)\n• Communicate with supervisors about realistic expectations\n\n⚖️ **Work-life balance:**\n• Set boundaries between work and personal time\n• Practice saying no to non-essential tasks\n• Make time for activities you enjoy\n• Consider if perfectionism is adding pressure\n\nWhat aspect of work/school is most challenging for you?",
            'severity': 'mild'
        }
    
    # General mental health awareness
    mental_health_keywords = ['therapy', 'counseling', 'mental health', 'wellbeing', 'self care', 'meditation', 'mindfulness']
    if any(keyword in message_lower for keyword in mental_health_keywords):
        session.distress_level = 2
        session.save()
        return {
            'message': "It's wonderful that you're thinking about your mental health! Taking care of your mental wellbeing is just as important as physical health:\n\n🌱 **Self-care basics:**\n• Regular exercise (even light walking)\n• Nutritious meals and staying hydrated\n• Adequate sleep (7-9 hours for most adults)\n• Social connections and support\n\n🧘 **Mental wellness practices:**\n• Mindfulness and meditation\n• Journaling or creative expression\n• Setting healthy boundaries\n• Professional therapy when needed\n\nWhat aspect of mental health would you like to explore further?",
            'severity': 'mild'
        }
    
    # Greeting responses
    greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(keyword in message_lower for keyword in greeting_keywords):
        session.distress_level = 1
        session.save()
        return {
            'message': "Hello! I'm glad you're here. I'm your mental health support assistant, and I'm here to listen and help in whatever way I can.\n\n💙 **I can help with:**\n• Stress and anxiety management\n• Coping strategies and techniques\n• Information about mental health resources\n• Just being someone to talk to\n\nWhat's on your mind today? Feel free to share whatever you're comfortable with.",
            'severity': 'mild'
        }
    
    # Breathing exercises
    breathing_keywords = ['breathing', 'breathe', 'breath']
    if any(keyword in message_lower for keyword in breathing_keywords):
        session.distress_level = 3
        session.save()
        return {
            'message': "Great choice! Breathing exercises are very effective for managing stress and anxiety.\n\n🌬️ **4-7-8 Breathing:**\n1. Breathe in through your nose for 4 counts\n2. Hold your breath for 7 counts\n3. Exhale through your mouth for 8 counts\n4. Repeat 3-4 times\n\n📦 **Box Breathing:**\n1. Breathe in for 4 counts\n2. Hold for 4 counts\n3. Breathe out for 4 counts\n4. Hold for 4 counts\n\nTry whichever feels more comfortable for you.",
            'severity': 'mild'
        }

    # Journaling requests
    journal_keywords = ['journal', 'writing', 'write', 'express', 'thoughts', 'feelings']
    if any(keyword in message_lower for keyword in journal_keywords):
        session.distress_level = 3
        session.save()
        return {
            'message': "Journaling is an excellent way to process your thoughts and emotions. Here are some prompts to get you started:\n\n📝 **Daily Reflection:**\n• How am I feeling right now?\n• What's one thing that went well today?\n• What's challenging me, and how can I address it?\n\n🙏 **Gratitude Practice:**\n• Write down 3 things you're grateful for\n• Include why each one matters to you\n\n🧩 **Problem-Solving:**\n• Describe a current challenge\n• List 3 possible solutions\n• Choose one small step to try",
            'severity': 'mild'
        }

    # Positive/gratitude responses
    positive_keywords = ['better', 'good', 'happy', 'grateful', 'thank']
    if any(keyword in message_lower for keyword in positive_keywords):
        session.distress_level = 1
        session.save()
        return {
            'message': "I'm so glad to hear you're feeling better! It's wonderful that you're taking care of your mental health.\n\n✨ **To Maintain Positive Momentum:**\n• Continue the practices that are helping\n• Notice and celebrate small wins\n• Build a toolkit of coping strategies\n• Stay connected with supportive people\n\nWhat's been most helpful for you recently?",
            'severity': 'mild'
        }

    # Default supportive response
    session.distress_level = 2
    session.save()
    return {
        'message': "Thank you for sharing that with me. I'm here to listen and support you through whatever you're experiencing.\n\n🤗 **Remember:**\n• Your feelings are valid\n• It's okay to not be okay sometimes\n• Seeking help is a sign of strength\n• You don't have to face challenges alone\n\nIs there something specific you'd like to talk about or explore? I'm here to help in whatever way feels most useful to you right now.",
        'severity': 'mild'
    }

@login_required
def mood_history(request):
    """View for displaying mood history"""
    # Get user's mood entries
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')
    
    return render(request, 'users/mood_history.html', {
        'mood_entries': mood_entries
    })