from django.urls import path
from . import views

app_name = 'non_soc'

urlpatterns = [
    path('dashboard/', views.non_soc_dashboard, name='dashboard'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:article_id>/', views.article_detail_view, name='article_detail'),
    path('progress/', views.user_progress, name='user_progress'),
    path('notifications/', views.notifications, name='notifications'),
    path('security-request/create/', views.create_security_request, name='create_security_request'),
    path('security-request/<int:request_id>/', views.security_request_detail, name='security_request_detail'),
    path('awareness/complete/<int:awareness_id>/', views.complete_awareness, name='complete_awareness'),
]