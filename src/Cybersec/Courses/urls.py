from django.urls import path
from . import views

app_name = 'courses'  # Make sure this is set for namespace to work

urlpatterns = [
    # Course browsing and enrollment
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),  # Make sure the URL pattern is correctly named as 'course_detail'
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    
    # Module details and completion
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('module/<int:module_id>/complete/', views.complete_module, name='complete_module'),
    
    # Course creation
    path('create/', views.create_course_start, name='create_course_start'),
    path('create/session/<int:session_id>/', views.course_creation_session, name='course_creation_session'),
    path('create/modules/<int:course_id>/', views.define_modules, name='define_modules'),
    path('create/chapters/<int:module_id>/', views.define_chapters, name='define_chapters'),
    path('create/content/<int:chapter_id>/', views.create_chapter_content, name='create_chapter_content'),
    
    # Learning paths
    path('learn/<int:enrollment_id>/', views.course_learn, name='course_learn'),
    path('chapter/<int:chapter_id>/', views.chapter_view, name='chapter_view'),
    path('submit-quiz/<int:chapter_id>/', views.submit_quiz, name='submit_quiz'),
    path('evaluate/<int:enrollment_id>/', views.evaluate_course, name='evaluate_course'),
    
    # Administrative views
    path('manage/', views.manage_courses, name='manage_courses'),
    path('edit/<int:course_id>/', views.edit_course, name='edit_course'),
    
    # Enrollment statistics
    path('stats/', views.enrollment_stats, name='enrollment_stats'),
]
