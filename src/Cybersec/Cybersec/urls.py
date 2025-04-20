"""
URL configuration for Cybersec project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from user import views as user_views
from user.views import index_view

urlpatterns = [
    # Main index route for proper redirection based on user type
    path('', index_view, name='index'),
    
    path('admin/', admin.site.urls),
    
    # User authentication
    path('signup/soc/', user_views.soc_user_signup, name='soc_user_signup'),
    path('login/soc/', user_views.soc_user_login, name='soc_user_login'),
    path('signup/non-soc/', user_views.non_soc_user_signup, name='non_soc_user_signup'),
    path('login/non-soc/', user_views.non_soc_user_login, name='non_soc_user_login'),
    path('logout/', user_views.user_logout, name='user_logout'),
    path('profile/', user_views.user_profile, name='user_profile'),
    
    # App-specific URLs
    path('soc/', include('Soc.urls', namespace='soc')),
    path('non-soc/', include('NonSoc.urls', namespace='non_soc')),
    
    # Dashboards
    path('dashboard/soc/', user_views.soc_dashboard, name='soc_dashboard'),
    path('dashboard/non-soc/', user_views.non_soc_dashboard, name='non_soc_dashboard'),
    
    # Include other app URLs
    path('articles/', include('Articles.urls', namespace='articles')),
    path('courses/', include('Courses.urls', namespace='courses')),
    path('tinymce/', include('tinymce.urls')),  # TinyMCE URLs
    path('awareness/', include('Awareness.urls', namespace='awareness')),
]

# Add serving of media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
