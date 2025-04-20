from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import HttpResponse, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from django import forms
from .models import SOCUser, NonSOCUser
from .forms import SOCUserSignupForm, SOCUserLoginForm, NonSOCUserSignupForm, NonSOCUserLoginForm, UserProfileForm, CustomPasswordChangeForm

User = get_user_model()

# Decorator functions
def admin_required(view_func):
    """Ensure only admin users can access a view"""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapped

def soc_user_required(view_func):
    """Ensure only SOC users can access a view"""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'soc':
            messages.error(request, "Access denied. SOC membership required.")
            return redirect('soc_user_login')
        return view_func(request, *args, **kwargs)
    return wrapped

def non_soc_user_required(view_func):
    """Ensure only Non-SOC users can access a view"""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'non_soc':
            messages.error(request, "Access denied. Non-SOC membership required.")
            return redirect('non_soc_user_login')
        return view_func(request, *args, **kwargs)
    return wrapped

# SOC user views
@login_required
@admin_required
def soc_user_signup(request):
    if request.method == 'POST':
        form = SOCUserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(admin_user=request.user)
            messages.success(request, f"SOC user account created for {user.username}")
            return redirect('admin_dashboard')
    else:
        form = SOCUserSignupForm()
    
    return render(request, 'user/soc_user_signup.html', {
        'form': form, 
        'title': 'Create SOC User Account'
    })

def soc_user_login(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'soc':
            return redirect('soc:dashboard')
        else:
            logout(request)
    
    if request.method == 'POST':
        form = SOCUserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            
            if not user:
                form.add_error(None, "Invalid username or password")
                return render(request, 'user/soc_user_login.html', {'form': form})
            
            if user.user_type != 'soc':
                form.add_error(None, "This account is not a SOC user account")
                return render(request, 'user/soc_user_login.html', {'form': form})
                
            login(request, user)
            next_url = request.GET.get('next', reverse('soc:dashboard'))
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts=request.get_host()):
                next_url = reverse('soc:dashboard')
            return redirect(next_url)
    else:
        form = SOCUserLoginForm()
    
    return render(request, 'user/soc_user_login.html', {'form': form})

@login_required
@soc_user_required
def soc_dashboard(request):
    return redirect('soc:dashboard')  # Redirect to the actual SOC app dashboard

# Non-SOC user views
def non_soc_user_signup(request):
    if request.user.is_authenticated:
        logout(request)
        
    if request.method == 'POST':
        form = NonSOCUserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully! You can now log in as {user.username}.")
            return redirect('non_soc_user_login')
    else:
        form = NonSOCUserSignupForm()
    
    return render(request, 'user/non_soc_user_signup.html', {
        'form': form,
        'title': 'Create Non-SOC User Account'
    })

def non_soc_user_login(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'non_soc':
            return redirect('non_soc:dashboard')
        else:
            logout(request)
    
    if request.method == 'POST':
        form = NonSOCUserLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Check if the input is an email or username
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                username = username_or_email

            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            
            if not user:
                form.add_error(None, "Invalid username/email or password")
                return render(request, 'user/non_soc_user_login.html', {'form': form})
            
            if user.user_type != 'non_soc':
                form.add_error(None, "This account is not a Non-SOC user account")
                return render(request, 'user/non_soc_user_login.html', {'form': form})
                
            login(request, user)
            next_url = request.GET.get('next', reverse('non_soc:dashboard'))
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts=request.get_host()):
                next_url = reverse('non_soc:dashboard')
            return redirect(next_url)
    else:
        form = NonSOCUserLoginForm()
    
    return render(request, 'user/non_soc_user_login.html', {'form': form})

@login_required
@non_soc_user_required
def non_soc_dashboard(request):
    return redirect('non_soc:dashboard')  # Redirect to the actual NonSOC app dashboard

# Common user views
@login_required
def user_profile(request):
    user = request.user
    profile_updated = False
    password_updated = False
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'update_profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            password_form = CustomPasswordChangeForm(user)
            
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated successfully!")
                profile_updated = True
                
        elif action == 'change_password':
            profile_form = UserProfileForm(instance=user)
            password_form = CustomPasswordChangeForm(user, request.POST)
            
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                user.last_password_change = timezone.now()
                user.save()
                messages.success(request, "Your password has been changed successfully!")
                password_updated = True
    else:
        profile_form = UserProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user)
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'profile_updated': profile_updated,
        'password_updated': password_updated,
        'user': user
    }
    
    # Different templates for SOC and Non-SOC users
    if user.user_type == 'soc':
        return render(request, 'user/soc_user_profile.html', context)
    else:
        return render(request, 'user/non_soc_user_profile.html', context)

@login_required
def user_logout(request):
    user_type = request.user.user_type
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    
    if user_type == 'soc':
        return redirect('soc_user_login')
    else:
        return redirect('non_soc_user_login')

# API endpoints for user data
@login_required
def user_api(request):
    user = request.user
    
    data = {
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'user_type': user.user_type,
    }
    
    if user.user_type == 'soc' and hasattr(user, 'soc_profile'):
        data.update({
            'role': user.soc_profile.role,
            'unique_identifier': user.soc_profile.unique_identifier,
            'profile_picture': request.build_absolute_uri(user.soc_profile.profile_picture.url) if user.soc_profile.profile_picture else None,
        })
    elif user.user_type == 'non_soc' and hasattr(user, 'non_soc_profile'):
        data.update({
            'department': user.non_soc_profile.department,
            'job_title': user.non_soc_profile.job_title,
            'profile_picture': request.build_absolute_uri(user.non_soc_profile.profile_picture.url) if user.non_soc_profile.profile_picture else None,
            'completed_trainings': user.non_soc_profile.completed_trainings,
            'security_awareness_level': {
                'level': user.non_soc_profile.security_awareness_level,
                'display': user.non_soc_profile.get_awareness_level_display(),
            }
        })
    
    return JsonResponse(data)

def index_view(request):
    """
    Main index view that redirects users to appropriate dashboards based on user type
    """
    if request.user.is_authenticated:
        # Direct to appropriate dashboard based on user type
        if hasattr(request.user, 'user_type'):
            if request.user.user_type == 'soc':
                return redirect('soc:dashboard')
            elif request.user.user_type == 'non_soc':
                return redirect('non_soc:dashboard')
        
        # Fallback based on user profile
        if hasattr(request.user, 'soc_profile') and request.user.soc_profile:
            return redirect('soc:dashboard')
        elif hasattr(request.user, 'non_soc_profile') and request.user.non_soc_profile:
            return redirect('non_soc:dashboard')
            
        # Final fallback to admin if user is staff
        if request.user.is_staff:
            return redirect('admin:index')
            
    # If not authenticated or no specific dashboard, show landing page
    return render(request, 'landing_page.html')
