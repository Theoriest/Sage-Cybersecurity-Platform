from django.urls import path
from . import views

app_name = 'soc'

urlpatterns = [
    path('dashboard/', views.soc_dashboard, name='dashboard'),
    
    # Incident management
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/<int:pk>/', views.incident_detail, name='incident_detail'),
    path('incidents/create/', views.incident_create, name='incident_create'),
    path('incidents/<int:pk>/update/', views.incident_update, name='incident_update'),
    
    # Alert management
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/<int:pk>/', views.alert_detail, name='alert_detail'),
    path('alerts/create/', views.alert_create, name='alert_create'),
    path('alerts/<int:pk>/update/', views.alert_update, name='alert_update'),
    path('alerts/<int:pk>/escalate/', views.alert_escalate, name='alert_escalate'),
    
    # Task management
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/update/', views.task_update, name='task_update'),
    
    # Reports
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:pk>/update/', views.report_update, name='report_update'),
    
    # Playbooks
    path('playbooks/', views.playbook_list, name='playbook_list'),
    path('playbooks/<int:pk>/', views.playbook_detail, name='playbook_detail'),
    path('playbooks/create/', views.playbook_create, name='playbook_create'),
    path('playbooks/<int:pk>/update/', views.playbook_update, name='playbook_update'),
    
    # Metrics
    path('metrics/', views.metrics_dashboard, name='metrics_dashboard'),
    path('metrics/list/', views.metric_list, name='metric_list'),
    path('metrics/<int:pk>/', views.metric_detail, name='metric_detail'),
    path('metrics/create/', views.metric_create, name='metric_create'),
    
    # Simple incident views
    path('incident/create/', views.create_incident, name='create_incident'),
    path('incident/<int:incident_id>/', views.incident_detail, name='incident_detail'),
    path('incident/<int:incident_id>/respond/', views.add_incident_response, name='add_incident_response'),
    
    # Security requests
    path('security-requests/', views.security_request_list, name='security_request_list'),
    path('security-requests/<int:request_id>/', views.security_request_detail, name='security_request_detail'),
    path('security-requests/<int:request_id>/resolve/', views.mark_security_request_resolved, name='mark_security_request_resolved'),
    path('security-requests/<int:request_id>/update-status/', views.update_security_request_status, name='update_security_request_status'),
    path('security-requests/<int:request_id>/respond/', views.add_security_request_response, name='add_security_request_response'),
]