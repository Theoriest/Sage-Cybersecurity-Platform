from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.http import HttpResponse
# Import the custom user model 
from django.contrib.auth import get_user_model
from Articles.models import Article
from Courses.models import Course, Enrollment, Progress
from user.views import non_soc_user_required, soc_user_required
from .models import SecurityRequest, UserNotification
from .forms import SecurityRequestForm
# Import Awareness app models
from Awareness.models import AwarenessModule, ModuleAttempt

# Get the custom user model
User = get_user_model()

@login_required
@non_soc_user_required
def non_soc_dashboard(request):
    """Display the non-SOC staff dashboard"""
    # Get user profile
    user_profile = request.user.non_soc_profile
    
    # Get recent articles - using 'status' field
    articles = Article.objects.filter(status='published').order_by('-created_at')[:2]
    
    # Get recent notifications
    notifications = UserNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:3]
    
    # We'll now use the Awareness app for awareness modules
    # Get security awareness modules through the relation with courses
    enrolled_courses = Enrollment.objects.filter(user=request.user, completed=True).values_list('course', flat=True)
    awareness_modules = []
    
    try:
        # Get modules for courses the user has completed
        awareness_modules = AwarenessModule.objects.filter(course__in=enrolled_courses)
        # Check which modules the user has passed
        for module in awareness_modules:
            module.is_passed = module.attempts.filter(user=request.user, passed=True).exists()
    except:
        awareness_modules = []
    
    # Get completed module attempts
    completed_awareness = ModuleAttempt.objects.filter(user=request.user, passed=True)
    
    # Get user's course enrollments for learning progress
    enrollments = Enrollment.objects.filter(user=request.user)[:3]
    
    # Calculate department average (all users in same department)
    department_avg_level = 0
    if hasattr(user_profile, 'department') and user_profile.department:
        department_users = User.objects.filter(
            non_soc_profile__department=user_profile.department
        ).exclude(id=request.user.id)
        
        if department_users.exists():
            completed_dept_courses = Enrollment.objects.filter(
                user__in=department_users,
                completed=True
            ).count()
            
            # Calculate average completed courses per department user
            department_avg_level = round(completed_dept_courses / department_users.count(), 1) if department_users.count() > 0 else 0
    
    # Get security requests - using the correct field name 'requester' instead of 'created_by'
    user_requests = SecurityRequest.objects.filter(
        requester=request.user
    ).order_by('-created_at')[:3]
    
    # Get enrollments with progress information
    for enrollment in enrollments:
        try:
            # Get total chapters in the course
            total_chapters = sum(module.chapters.count() for module in enrollment.course.modules.all())
            if total_chapters > 0:
                # Get completed chapters
                completed_chapters = Progress.objects.filter(
                    enrollment=enrollment, 
                    completed=True
                ).count()
                # Calculate percentage
                enrollment.progress_value = int((completed_chapters / total_chapters) * 100)
            else:
                enrollment.progress_value = 0
        except Exception as e:
            # Handle any errors gracefully
            print(f"Error calculating progress: {e}")
            enrollment.progress_value = 0
    
    # Calculate completed trainings - count both completed courses and awareness modules
    completed_trainings = Enrollment.objects.filter(
        user=request.user, 
        completed=True
    ).count()
    
    # Add completed awareness modules from new system
    completed_trainings += completed_awareness.count()
    
    context = {
        'articles': articles,
        'notifications': notifications,
        'awareness_modules': awareness_modules,
        'completed_awareness': [attempt.module for attempt in completed_awareness],
        'user_requests': user_requests,
        'awareness_level_display': user_profile.get_awareness_level_display(),
        'completed_trainings': completed_trainings,
        'department_avg_level': department_avg_level,
        'enrollments': enrollments,
    }
    
    return render(request, 'NonSoc/nonsoc_dashboard.html', context)

@login_required
@non_soc_user_required
def article_list(request):
    """List of security articles for non-SOC users"""
    # Filter articles by category if provided
    category = request.GET.get('category')
    search = request.GET.get('search')
    articles = Article.objects.filter(
        status='published',  # Only published articles
        visibility__in=['public', 'non_soc']  # Only appropriate visibility
    )
    if category:
        articles = articles.filter(categories__name=category)
    
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search)
        )
    context = {
        'articles': articles,
        'search_query': search,
        'category': category,
    }
    return render(request, 'NonSoc/article_list.html', context)

@login_required
@non_soc_user_required
def article_detail_view(request, article_id):
    """View a specific article's details"""
    # Use status='published' instead of is_published=True
    article = get_object_or_404(Article, id=article_id, status='published')
    context = {
        'article': article
    }
    return render(request, 'NonSoc/article_detail.html', context)

@login_required
@non_soc_user_required
def user_progress(request):
    """View user's learning progress"""
    # Get all user's course enrollments
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    # Calculate progress percentage for each enrollment
    for enrollment in enrollments:
        try:
            # Get total chapters in the course
            total_chapters = sum(module.chapters.count() for module in enrollment.course.modules.all())
            if total_chapters > 0:
                # Get completed chapters
                completed_chapters = Progress.objects.filter(
                    enrollment=enrollment, 
                    completed=True
                ).count()
                # Calculate percentage
                enrollment.progress_percentage = int((completed_chapters / total_chapters) * 100)
            else:
                enrollment.progress_percentage = 0
        except Exception as e:
            # Handle any errors gracefully
            print(f"Error calculating progress: {e}")
            enrollment.progress_percentage = 0
    # Get user awareness data
    user_profile = request.user.non_soc_profile
    awareness_level = getattr(user_profile, 'security_awareness_level', 1)
    awareness_display = user_profile.get_awareness_level_display() if hasattr(user_profile, 'get_awareness_level_display') else "Beginner"
    # Calculate completed trainings
    completed_trainings = Enrollment.objects.filter(
        user=request.user, 
        completed=True
    ).count()
    # Count completed awareness modules from the new system only
    try:
        completed_trainings += ModuleAttempt.objects.filter(user=request.user, passed=True).distinct('module').count()
    except:
        # If distinct is not supported (e.g., SQLite)
        module_counts = ModuleAttempt.objects.filter(
            user=request.user, 
            passed=True
        ).values('module').annotate(count=Count('module'))
        completed_trainings += len(module_counts)
    # Update the profile with the accurate count
    user_profile.completed_trainings = completed_trainings
    user_profile.save()
    progress_percentage = min(awareness_level * 20, 100)  # Calculate percentage (20% per level)
    context = {
        'enrollments': enrollments,
        'awareness_level': awareness_level,
        'awareness_display': awareness_display,        
        'completed_trainings': completed_trainings,    
        'progress_percentage': progress_percentage,
    }
    return render(request, 'NonSoc/user_progress.html', context)

@login_required
@non_soc_user_required
def notifications(request):
    """View and manage user notifications"""
    # Get all notifications for the current user
    notifications = request.user.notifications.all().order_by('-created_at')
    # Count unread notifications
    unread_count = notifications.filter(is_read=False).count()
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'NonSoc/notifications.html', context)

@login_required
def create_security_request(request):
    """Create a new security request"""
    if request.method == 'POST':
        form = SecurityRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.requester = request.user
            request_obj.save()
            return redirect('non_soc:dashboard')
    else:
        form = SecurityRequestForm()
    return render(request, 'NonSoc/create_security_request.html', {'form': form})

@login_required
def security_request_detail(request, request_id):
    """View details of a specific security request"""
    security_request = get_object_or_404(SecurityRequest, id=request_id, requester=request.user)
    # Fix: Use correct capitalization for template path (NonSoc instead of nonsoc)
    return render(request, 'NonSoc/security_request_detail.html', {'security_request': security_request})

@login_required
def complete_awareness(request, awareness_id):
    """Handle legacy awareness module URLs"""
    messages.info(request, "Our awareness modules have been upgraded. Please check your dashboard for new modules.")
    return redirect('non_soc:dashboard')