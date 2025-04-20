from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('non-soc-logout/', auth_views.LogoutView.as_view(
        template_name='users/non_soc_logout.html',
        next_page='login'
    ), name='non_soc_logout'),
]