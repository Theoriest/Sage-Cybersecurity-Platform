from django.urls import path
from . import views

urlpatterns = [
    path('soc/signup/', views.soc_user_signup, name='soc_user_signup'),
    path('soc/login/', views.soc_user_login, name='soc_user_login'),
    path('non-soc/signup/', views.non_soc_user_signup, name='non_soc_user_signup'),
    path('non-soc/login/', views.non_soc_user_login, name='non_soc_user_login'),
    path('logout/', views.user_logout, name='user_logout'),
]
