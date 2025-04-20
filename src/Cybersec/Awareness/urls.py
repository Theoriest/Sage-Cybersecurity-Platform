from django.urls import path
from . import views

app_name = 'awareness'

urlpatterns = [
    # Module management (SOC users)
    path('modules/', views.module_list, name='module_list'),
    path('modules/create/', views.create_module, name='create_module'),
    path('modules/<int:module_id>/', views.module_detail, name='module_detail'),
    path('modules/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('modules/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    
    # Question management
    path('modules/<int:module_id>/questions/', views.manage_questions, name='manage_questions'),
    path('modules/<int:module_id>/questions/add/', views.add_question, name='add_question'),
    path('questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    
    # AI generation
    path('modules/<int:module_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    
    # User-facing module interaction
    path('module/<int:module_id>/', views.take_module, name='take_module'),
    path('module/<int:module_id>/start/', views.start_module, name='start_module'),
    path('module/<int:module_id>/complete/', views.complete_module, name='complete_module'),
    path('module/<int:attempt_id>/review/', views.review_attempt, name='review_attempt'),
    
    # Analytics
    path('analytics/', views.module_analytics, name='analytics'),
    path('analytics/module/<int:module_id>/', views.module_detail_analytics, name='module_analytics'),
]
