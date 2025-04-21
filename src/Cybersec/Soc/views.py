from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.defaultfilters import register
from datetime import timedelta

from .models import (
    SecurityIncident,
    SecurityAlert,
    SocTask,
    SecurityReport,
    PlaybookTemplate,
    SecurityMetric,
    MetricDataPoint,
    Incident,
    IncidentResponse
)
from .forms import (
    SecurityIncidentForm,
    SecurityAlertForm,
    SocTaskForm,
    SecurityReportForm,
    PlaybookTemplateForm,
    SecurityMetricForm,
    IncidentForm,
    IncidentResponseForm
)

def is_soc_user(user):
    """Check if user is a SOC user"""
    return user.is_authenticated and hasattr(user, 'soc_profile')

# Custom decorator for SOC access
def soc_required(view_func):
    """Decorator to ensure only SOC members can access certain views"""
    def wrapped(request, *args, **kwargs):
        if not is_soc_user(request.user):
            messages.error(request, "Access denied. SOC membership required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped

@register.filter
def split_affected_systems(value):
    """Split affected systems by line breaks and commas"""
    if not value:
        return []
    
    systems = []
    lines = value.split('\n')
    for line in lines:
        items = [item.strip() for item in line.split(',')]
        systems.extend([item for item in items if item])
    return systems

@login_required
@soc_required
def soc_dashboard(request):
    """Main SOC dashboard view"""
    # Get counts for key metrics
    new_incidents = SecurityIncident.objects.filter(status='new').count()
    in_progress_incidents = SecurityIncident.objects.filter(status='in_progress').count()
    new_alerts = SecurityAlert.objects.filter(status='new').count()
    my_tasks = SocTask.objects.filter(assigned_to=request.user).count()
    
    # Get recent incidents
    recent_incidents = SecurityIncident.objects.all().order_by('-created_at')[:5]
    
    # Get high severity alerts
    critical_alerts = SecurityAlert.objects.filter(
        severity__in=['critical', 'high']
    ).order_by('-created_at')[:5]
    
    # Get upcoming tasks
    upcoming_tasks = SocTask.objects.filter(
        assigned_to=request.user,
        status__in=['new', 'in_progress']
    ).order_by('due_date')[:5]
    
    # Get recent reports
    recent_reports = SecurityReport.objects.all().order_by('-created_at')[:5]
    
    # Get recent articles (added)
    from Articles.models import Article
    recent_articles = Article.objects.all().order_by('-created_at')[:5]
    
    context = {
        'new_incidents': new_incidents,
        'in_progress_incidents': in_progress_incidents,
        'new_alerts': new_alerts,
        'my_tasks': my_tasks,
        'recent_incidents': recent_incidents,
        'critical_alerts': critical_alerts,
        'upcoming_tasks': upcoming_tasks,
        'recent_reports': recent_reports,
        'recent_articles': recent_articles,  # Added recent articles
    }
    
    return render(request, 'soc/dashboard.html', context)

@login_required
def dashboard(request):
    open_incidents = Incident.objects.filter(status__in=['open', 'in_progress']).order_by('-created_at')
    assigned_incidents = Incident.objects.filter(assigned_to=request.user).order_by('-created_at')
    
    context = {
        'open_incidents': open_incidents,
        'assigned_incidents': assigned_incidents
    }
    return render(request, 'soc/dashboard.html', context)

@login_required
def create_incident(request):
    if request.method == 'POST':
        form = IncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reporter = request.user
            incident.save()
            return redirect('soc:incident_detail', pk=incident.id)  # Updated namespace and parameter name
    else:
        form = IncidentForm()
    
    return render(request, 'soc/create_incident.html', {'form': form})

@login_required
def incident_detail(request, pk=None, incident_id=None):
    # Support both parameter names for flexibility
    id_to_use = pk if pk is not None else incident_id
    incident = get_object_or_404(Incident, id=id_to_use)
    responses = incident.responses.all().order_by('created_at')
    
    context = {
        'incident': incident,
        'responses': responses
    }
    return render(request, 'soc/incident_detail.html', context)

@login_required
def add_incident_response(request, pk=None, incident_id=None):
    # Support both parameter names for flexibility
    id_to_use = pk if pk is not None else incident_id
    incident = get_object_or_404(Incident, id=id_to_use)
    
    if request.method == 'POST':
        form = IncidentResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.incident = incident
            response.responder = request.user
            response.save()
            return redirect('soc:incident_detail', pk=incident.id)  # Updated namespace and parameter name
    else:
        form = IncidentResponseForm()
    
    return render(request, 'soc/add_response.html', {'form': form, 'incident': incident})

# Incident management views
@login_required
@soc_required
def incident_list(request):
    """View for listing all security incidents"""
    # Get filter parameters
    status = request.GET.get('status')
    severity = request.GET.get('severity')
    assigned_to = request.GET.get('assigned_to')
    
    incidents = SecurityIncident.objects.all()
    
    # Apply filters
    if status:
        incidents = incidents.filter(status=status)
    if severity:
        incidents = incidents.filter(severity=severity)
    if assigned_to:
        if assigned_to == 'me':
            incidents = incidents.filter(assigned_to=request.user.soc_profile)
        elif assigned_to == 'unassigned':
            incidents = incidents.filter(assigned_to__isnull=True)
        else:
            incidents = incidents.filter(assigned_to__id=assigned_to)
    
    # Calculate incident statistics
    incident_stats = {
        'critical': SecurityIncident.objects.filter(severity='critical').count(),
        'in_progress': SecurityIncident.objects.filter(status='in_progress').count(),
        'new': SecurityIncident.objects.filter(status='open').count(),
        'resolved': SecurityIncident.objects.filter(status__in=['resolved', 'closed']).count(),
    }
    
    # Order by latest first
    incidents = incidents.order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(incidents, 15)  # Show 15 incidents per page
    incidents = paginator.get_page(page)
    
    context = {
        'incidents': incidents,
        'incident_stats': incident_stats,
        'status_choices': dict(SecurityIncident._meta.get_field('status').choices),
        'severity_choices': dict(SecurityIncident._meta.get_field('severity').choices),
        'current_filters': {
            'status': status,
            'severity': severity,
            'assigned_to': assigned_to,
        }
    }
    return render(request, 'soc/incident_list.html', context)

@login_required
@soc_required
def incident_detail(request, pk):
    """View for viewing a security incident's details"""
    incident = get_object_or_404(SecurityIncident, pk=pk)
    related_alerts = incident.related_alerts.all()
    related_reports = incident.related_reports.all()
    
    context = {
        'incident': incident,
        'related_alerts': related_alerts,
        'related_reports': related_reports,
    }
    return render(request, 'soc/incident_detail.html', context)

@login_required
@soc_required
def incident_create(request):
    """View for creating a new security incident"""
    if request.method == 'POST':
        form = SecurityIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reported_by = request.user  # Set the current user as reporter
            incident.save()
            messages.success(request, 'Security incident created successfully.')
            return redirect('soc:incident_detail', pk=incident.pk)
    else:
        form = SecurityIncidentForm()
    
    context = {'form': form, 'title': 'Create Security Incident'}
    return render(request, 'soc/incident_form.html', context)

@login_required
@soc_required
def incident_update(request, pk):
    """View for updating an existing security incident"""
    incident = get_object_or_404(SecurityIncident, pk=pk)
    
    if request.method == 'POST':
        form = SecurityIncidentForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            messages.success(request, 'Security incident updated successfully.')
            return redirect('soc:incident_detail', pk=incident.pk)
    else:
        form = SecurityIncidentForm(instance=incident)
    
    context = {'form': form, 'title': 'Update Security Incident', 'incident': incident}
    return render(request, 'soc/incident_form.html', context)

# Alert management views
@login_required
@soc_required
def alert_list(request):
    """View for listing security alerts"""
    # Get filter parameters
    status = request.GET.get('status')
    severity = request.GET.get('severity')
    false_positive = request.GET.get('false_positive')
    search = request.GET.get('search')
    
    alerts = SecurityAlert.objects.all()
    
    # Apply filters
    if status:
        alerts = alerts.filter(status=status)
    if severity:
        alerts = alerts.filter(severity=severity)
    if false_positive:
        is_false_positive = false_positive == 'true'
        alerts = alerts.filter(false_positive=is_false_positive)
    if search:
        alerts = alerts.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Calculate alert stats
    alert_stats = {
        'critical': SecurityAlert.objects.filter(severity='critical').count(),
        'high': SecurityAlert.objects.filter(severity='high').count(),
        'medium': SecurityAlert.objects.filter(severity='medium').count(),
        'low': SecurityAlert.objects.filter(severity='low').count(),
    }
    
    # Order by latest first
    alerts = alerts.order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(alerts, 15)  # 15 alerts per page
    alerts = paginator.get_page(page)
    
    context = {
        'alerts': alerts,
        'alert_stats': alert_stats,
        'status_choices': dict(SecurityAlert._meta.get_field('status').choices),
        'severity_choices': dict(SecurityAlert._meta.get_field('severity').choices),
        'current_filters': {
            'status': status,
            'severity': severity,
            'false_positive': false_positive,
            'search': search,
        }
    }
    return render(request, 'soc/alert_list.html', context)

@login_required
@soc_required
def alert_detail(request, pk):
    """View for viewing a security alert's details"""
    alert = get_object_or_404(SecurityAlert, pk=pk)
    
    context = {
        'alert': alert,
    }
    return render(request, 'soc/alert_detail.html', context)

@login_required
@soc_required
def alert_create(request):
    """View for creating a new security alert"""
    if request.method == 'POST':
        form = SecurityAlertForm(request.POST)
        if form.is_valid():
            alert = form.save()
            messages.success(request, 'Security alert created successfully.')
            return redirect('soc:alert_detail', pk=alert.pk)
    else:
        form = SecurityAlertForm()
    
    context = {'form': form, 'title': 'Create Security Alert'}
    return render(request, 'soc/alert_form.html', context)

@login_required
@soc_required
def alert_update(request, pk):
    """View for updating an existing security alert"""
    alert = get_object_or_404(SecurityAlert, pk=pk)
    
    if request.method == 'POST':
        form = SecurityAlertForm(request.POST, instance=alert)
        if form.is_valid():
            form.save()
            messages.success(request, 'Security alert updated successfully.')
            return redirect('soc:alert_detail', pk=alert.pk)
    else:
        form = SecurityAlertForm(instance=alert)
    
    context = {'form': form, 'title': 'Update Security Alert', 'alert': alert}
    return render(request, 'soc/alert_form.html', context)

@login_required
@soc_required
def alert_escalate(request, pk):
    """View for escalating an alert to an incident"""
    alert = get_object_or_404(SecurityAlert, pk=pk)
    
    if request.method == 'POST':
        form = SecurityIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reported_by = request.user
            incident.save()
            
            # Link alert to the new incident
            alert.related_incident = incident
            alert.status = 'closed'  # Close the alert
            alert.save()
            
            messages.success(request, 'Alert escalated to incident successfully.')
            return redirect('soc:incident_detail', pk=incident.pk)
    else:
        # Pre-fill the incident form with alert information
        initial_data = {
            'title': f"Incident from alert: {alert.title}",
            'description': alert.description,
            'details': f"<p>Escalated from alert #{alert.id}</p><p>{alert.description}</p>",
            'severity': alert.severity,
        }
        form = SecurityIncidentForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Escalate Alert to Incident',
        'alert': alert
    }
    return render(request, 'soc/incident_form.html', context)

# Task management views
@login_required
@soc_required
def task_list(request):
    """View for listing SOC tasks"""
    # Get filter parameters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    assigned_to = request.GET.get('assigned_to')
    
    tasks = SocTask.objects.all()
    
    # Apply filters
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if assigned_to:
        if assigned_to == 'me':
            tasks = tasks.filter(assigned_to=request.user.soc_profile)
        elif assigned_to == 'unassigned':
            tasks = tasks.filter(assigned_to__isnull=True)
        else:
            tasks = tasks.filter(assigned_to__id=assigned_to)
    
    # Calculate task statistics
    now = timezone.now().date()
    task_stats = {
        'total': SocTask.objects.count(),
        'in_progress': SocTask.objects.filter(status='in_progress').count(),
        'overdue': SocTask.objects.filter(due_date__lt=now).exclude(status='completed').count(),
        'completed': SocTask.objects.filter(status='completed').count(),
    }
    
    # Default: sort by due date if available, then by priority
    tasks = tasks.order_by('due_date', '-priority', '-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(tasks, 20)  # Show 20 tasks per page
    tasks = paginator.get_page(page)
    
    context = {
        'tasks': tasks,
        'task_stats': task_stats,
        'now': now,
        'status_choices': dict(SocTask._meta.get_field('status').choices),
        'priority_choices': dict(SocTask._meta.get_field('priority').choices),
        'current_filters': {
            'status': status,
            'priority': priority,
            'assigned_to': assigned_to,
        }
    }
    return render(request, 'soc/task_list.html', context)

@login_required
@soc_required
def task_detail(request, pk):
    """View for viewing a SOC task's details"""
    task = get_object_or_404(SocTask, pk=pk)
    
    context = {
        'task': task,
    }
    return render(request, 'soc/task_detail.html', context)

@login_required
@soc_required
def task_create(request):
    """View for creating a new SOC task"""
    if request.method == 'POST':
        form = SocTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully.')
            return redirect('soc:task_detail', pk=task.pk)
    else:
        form = SocTaskForm()
    
    context = {'form': form, 'title': 'Create Task'}
    return render(request, 'soc/task_form.html', context)

@login_required
@soc_required
def task_update(request, pk):
    """View for updating an existing SOC task"""
    task = get_object_or_404(SocTask, pk=pk)
    
    if request.method == 'POST':
        form = SocTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('soc:task_detail', pk=task.pk)
    else:
        form = SocTaskForm(instance=task)
    
    context = {'form': form, 'title': 'Update Task', 'task': task}
    return render(request, 'soc/task_form.html', context)

# Playbook views
@login_required
@soc_required
def playbook_list(request):
    """View for listing incident response playbooks"""
    category = request.GET.get('category')
    
    playbooks = PlaybookTemplate.objects.all()
    
    if category:
        playbooks = playbooks.filter(category=category)
    
    playbooks = playbooks.order_by('title')
    
    context = {
        'playbooks': playbooks,
        'category_choices': dict(PlaybookTemplate._meta.get_field('category').choices),
        'current_filters': {
            'category': category,
        }
    }
    return render(request, 'soc/playbook_list.html', context)

@login_required
@soc_required
def playbook_detail(request, pk):
    """View for viewing a playbook's details"""
    playbook = get_object_or_404(PlaybookTemplate, pk=pk)
    
    context = {
        'playbook': playbook,
    }
    return render(request, 'soc/playbook_detail.html', context)

@login_required
@soc_required
def playbook_create(request):
    """View for creating a new playbook"""
    if request.method == 'POST':
        form = PlaybookTemplateForm(request.POST)
        if form.is_valid():
            playbook = form.save(commit=False)
            playbook.created_by = request.user
            playbook.save()
            messages.success(request, 'Playbook created successfully.')
            return redirect('soc:playbook_detail', pk=playbook.pk)
    else:
        form = PlaybookTemplateForm()
    
    context = {'form': form, 'title': 'Create Playbook'}
    return render(request, 'soc/playbook_form.html', context)

@login_required
@soc_required
def playbook_update(request, pk):
    """View for updating an existing playbook"""
    playbook = get_object_or_404(PlaybookTemplate, pk=pk)
    
    if request.method == 'POST':
        form = PlaybookTemplateForm(request.POST, instance=playbook)
        if form.is_valid():
            form.save()
            messages.success(request, 'Playbook updated successfully.')
            return redirect('soc:playbook_detail', pk=playbook.pk)
    else:
        form = PlaybookTemplateForm(instance=playbook)
    
    context = {'form': form, 'title': 'Update Playbook', 'playbook': playbook}
    return render(request, 'soc/playbook_form.html', context)

# Report management views
@login_required
@soc_required
def report_list(request):
    """View for listing security reports"""
    report_type = request.GET.get('report_type')
    
    reports = SecurityReport.objects.all()
    
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    reports = reports.order_by('-created_at')
    
    context = {
        'reports': reports,
        'report_type_choices': dict(SecurityReport._meta.get_field('report_type').choices),
        'current_filters': {
            'report_type': report_type,
        }
    }
    return render(request, 'soc/report_list.html', context)

@login_required
@soc_required
def report_detail(request, pk):
    """View for viewing a security report's details"""
    report = get_object_or_404(SecurityReport, pk=pk)
    
    context = {
        'report': report,
    }
    return render(request, 'soc/report_detail.html', context)

@login_required
@soc_required
def report_create(request):
    """View for creating a new security report"""
    if request.method == 'POST':
        form = SecurityReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            report.save()
            # Save many-to-many relationships
            form.save_m2m()
            messages.success(request, 'Security report created successfully.')
            return redirect('soc:report_detail', pk=report.pk)
    else:
        form = SecurityReportForm()
    
    context = {'form': form, 'title': 'Create Security Report'}
    return render(request, 'soc/report_form.html', context)

@login_required
@soc_required
def report_update(request, pk):
    """View for updating an existing security report"""
    report = get_object_or_404(SecurityReport, pk=pk)
    
    if request.method == 'POST':
        form = SecurityReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Security report updated successfully.')
            return redirect('soc:report_detail', pk=report.pk)
    else:
        form = SecurityReportForm(instance=report)
    
    context = {'form': form, 'title': 'Update Security Report', 'report': report}
    return render(request, 'soc/report_form.html', context)

# Metrics dashboard view
@login_required
@soc_required
def metrics_dashboard(request):
    """View for SOC metrics dashboard"""
    # Get all active metrics
    metrics = SecurityMetric.objects.all()
    
    # Calculate progress percentage for each metric
    for metric in metrics:
        if metric.target_value > 0:
            # Calculate percentage based on whether we want to maximize or minimize the metric
            # For example, "time to detect" should be minimized, but "detection rate" should be maximized
            if metric.unit.lower() in ['hours', 'minutes', 'seconds', 'days']:
                # For metrics where lower is better (like time)
                if metric.current_value <= metric.target_value:
                    metric.progress_percentage = 100
                else:
                    # Higher than target (worse) - calculate how far over
                    over_percentage = ((metric.current_value - metric.target_value) / metric.target_value) * 100
                    metric.progress_percentage = max(0, 100 - min(over_percentage, 100))
            else:
                # For metrics where higher is better (like rates, percentages)
                raw_percentage = (metric.current_value / metric.target_value) * 100
                metric.progress_percentage = min(raw_percentage, 100)  # Cap at 100%
        else:
            metric.progress_percentage = 0
    
    # Get incident metrics
    total_incidents = SecurityIncident.objects.count()
    open_incidents = SecurityIncident.objects.filter(
        status__in=['new', 'in_progress', 'under_review']
    ).count()
    resolved_incidents = SecurityIncident.objects.filter(
        status__in=['resolved', 'closed']
    ).count()
    
    # Calculate resolution rate
    resolution_rate = 0
    if total_incidents > 0:
        resolution_rate = int((resolved_incidents / total_incidents) * 100)
    
    # Calculate average resolution time (in hours)
    avg_resolution_time = "N/A"
    resolved_with_time = SecurityIncident.objects.filter(
        status__in=['resolved', 'closed']
    ).exclude(updated_at=None)
    
    if resolved_with_time.exists():
        total_hours = 0
        count = 0
        for incident in resolved_with_time:
            # Calculate time difference in hours
            time_diff = (incident.updated_at - incident.created_at).total_seconds() / 3600
            total_hours += time_diff
            count += 1
        
        if count > 0:
            avg_hours = total_hours / count
            avg_resolution_time = f"{avg_hours:.1f}"  # Format to 1 decimal place
    
    # Incidents by severity
    incidents_by_severity = (
        SecurityIncident.objects.values('severity')
        .annotate(count=Count('id'))
        .order_by('severity')
    )
    
    # Time trends - last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    incidents_by_day = (
        SecurityIncident.objects.filter(created_at__gte=thirty_days_ago)
        .extra(select={'day': 'date(created_at)'})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    
    context = {
        'metrics': metrics,
        'total_incidents': total_incidents,
        'open_incidents': open_incidents,
        'resolution_rate': resolution_rate,
        'avg_resolution_time': avg_resolution_time,
        'incidents_by_severity': incidents_by_severity,
        'incidents_by_day': incidents_by_day,
    }
    return render(request, 'soc/metrics_dashboard.html', context)

@login_required
@soc_required
def metric_list(request):
    """View for listing and managing security metrics"""
    metrics = SecurityMetric.objects.all().order_by('name')
    
    context = {
        'metrics': metrics,
    }
    return render(request, 'soc/metric_list.html', context)

@login_required
@soc_required
def metric_detail(request, pk):
    """View for viewing a security metric's details and history"""
    metric = get_object_or_404(SecurityMetric, pk=pk)
    history = metric.data_points.all().order_by('-recorded_at')[:30]
    
    context = {
        'metric': metric,
        'history': history,
    }
    return render(request, 'soc/metric_detail.html', context)

@login_required
@soc_required
def metric_create(request):
    """View for creating a new security metric"""
    if request.method == 'POST':
        form = SecurityMetricForm(request.POST)
        if form.is_valid():
            metric = form.save(commit=False)
            metric.updated_by = request.user
            metric.save()
            
            # Create the initial data point
            MetricDataPoint.objects.create(
                metric=metric,
                value=metric.current_value,
                notes=f"Initial value set by {request.user.username}"
            )
            
            messages.success(request, 'Security metric created successfully.')
            return redirect('soc:metric_detail', pk=metric.pk)
    else:
        form = SecurityMetricForm()
    
    context = {'form': form, 'title': 'Create Security Metric'}
    return render(request, 'soc/metric_form.html', context)

@login_required
@soc_required
def metric_update(request, pk):
    """View for updating an existing security metric"""
    metric = get_object_or_404(SecurityMetric, pk=pk)
    old_value = metric.current_value
    
    if request.method == 'POST':
        form = SecurityMetricForm(request.POST, instance=metric)
        if form.is_valid():
            metric = form.save(commit=False)
            metric.updated_by = request.user
            metric.save()
            
            # If value changed, create a new data point
            if metric.current_value != old_value:
                MetricDataPoint.objects.create(
                    metric=metric,
                    value=metric.current_value,
                    notes=request.POST.get('data_point_notes', '')
                )
            
            messages.success(request, 'Security metric updated successfully.')
            return redirect('soc:metric_detail', pk=metric.pk)
    else:
        form = SecurityMetricForm(instance=metric)
    
    context = {
        'form': form,
        'title': 'Update Security Metric',
        'metric': metric,
        'show_data_point_notes': True
    }
    return render(request, 'soc/metric_form.html', context)

# Security Request views
@login_required
@soc_required
def security_request_list(request):
    """View for listing all security requests"""
    # Get filter parameters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    # Start with all security requests
    from NonSoc.models import SecurityRequest
    security_requests = SecurityRequest.objects.all()
    
    # Apply filters
    if status:
        security_requests = security_requests.filter(status=status)
    if priority:
        security_requests = security_requests.filter(priority=priority)
    if category:
        security_requests = security_requests.filter(category=category)
    if search:
        security_requests = security_requests.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(requester__username__icontains=search) |
            Q(requester__first_name__icontains=search) |
            Q(requester__last_name__icontains=search)
        )
    
    # Order by latest first
    security_requests = security_requests.order_by('-created_at')
    
    # Calculate statistics for quick overview
    request_stats = {
        'total': SecurityRequest.objects.count(),
        'open': SecurityRequest.objects.filter(status='new').count(),
        'in_progress': SecurityRequest.objects.filter(status='in_progress').count(),
        'resolved': SecurityRequest.objects.filter(status__in=['resolved', 'closed']).count(),
    }
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(security_requests, 20)  # Show 20 requests per page
    security_requests = paginator.get_page(page)
    
    context = {
        'security_requests': security_requests,
        'request_stats': request_stats,
        'current_filters': {
            'status': status,
            'priority': priority,
            'category': category,
            'search': search,
        }
    }
    return render(request, 'soc/security_request_list.html', context)

@login_required
@soc_required
def security_request_detail(request, request_id):
    """View for viewing a security request's details"""
    from NonSoc.models import SecurityRequest
    security_request = get_object_or_404(SecurityRequest, id=request_id)
    
    context = {
        'security_request': security_request,
    }
    return render(request, 'soc/security_request_detail.html', context)

@login_required
@soc_required
def mark_security_request_resolved(request, request_id):
    """Mark a security request as resolved"""
    from NonSoc.models import SecurityRequest
    security_request = get_object_or_404(SecurityRequest, id=request_id)
    security_request.status = 'resolved'
    security_request.resolved_at = timezone.now()
    security_request.save()
    
    # Create a notification for the requester
    from NonSoc.models import UserNotification
    UserNotification.objects.create(
        user=security_request.requester,
        title="Request Resolved",
        message=f"Your security request '{security_request.title}' has been resolved.",
        notification_type='request_update'
    )
    
    messages.success(request, f"Security request #{request_id} has been marked as resolved.")
    return redirect('soc:security_request_list')

@login_required
@soc_required
def update_security_request_status(request, request_id):
    """Update the status of a security request"""
    from NonSoc.models import SecurityRequest
    security_request = get_object_or_404(SecurityRequest, id=request_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(SecurityRequest.STATUS_CHOICES).keys():
            # If request is being moved to resolved status, set resolved timestamp
            if status == 'resolved' and security_request.status != 'resolved':
                security_request.resolved_at = timezone.now()
                
            security_request.status = status
            security_request.save()
            
            # Create a notification for the requester
            from NonSoc.models import UserNotification
            UserNotification.objects.create(
                user=security_request.requester,
                title="Request Status Updated",
                message=f"Your security request '{security_request.title}' has been updated to {security_request.get_status_display()}.",
                notification_type='request_update'
            )
            
            messages.success(request, f"Security request status updated to '{security_request.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status value.")
    
    return redirect('soc:security_request_detail', request_id=security_request.id)

@login_required
@soc_required
def add_security_request_response(request, request_id):
    """Add a response to a security request"""
    from NonSoc.models import SecurityRequest, SecurityRequestResponse
    security_request = get_object_or_404(SecurityRequest, id=request_id)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            # Create the response
            SecurityRequestResponse.objects.create(
                security_request=security_request,
                responder=request.user,
                message=message
            )
            
            # Update the request's last activity timestamp
            security_request.updated_at = timezone.now()
            security_request.save()
            
            # Create a notification for the requester
            from NonSoc.models import UserNotification
            UserNotification.objects.create(
                user=security_request.requester,
                title="New Response to Your Request",
                message=f"Your security request '{security_request.title}' has received a new response.",
                notification_type='request_response'
            )
            
            messages.success(request, "Your response has been added successfully.")
        else:
            messages.error(request, "Response message cannot be empty.")
    
    return redirect('soc:security_request_detail', request_id=security_request.id)
