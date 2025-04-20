from django.db import models
from django.conf import settings
from tinymce.models import HTMLField
from django.contrib.auth import get_user_model

User = get_user_model()

# Status choices for various models
STATUS_CHOICES = [
    ('new', 'New'),
    ('in_progress', 'In Progress'),
    ('under_review', 'Under Review'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
]

# Severity choices for incidents and alerts
SEVERITY_CHOICES = [
    ('critical', 'Critical'),
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
    ('info', 'Informational'),
]

class SecurityIncident(models.Model):
    """Model for security incidents that SOC team members need to address"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    details = HTMLField()  # Rich text field for detailed incident information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Assignment and ownership
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_security_incidents'  # Changed from 'assigned_incidents'
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='reported_security_incidents'  # Changed from 'reported_incidents'
    )
    
    # Incident metadata
    affected_systems = models.TextField()
    remediation_steps = HTMLField(null=True, blank=True)
    resolution_summary = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()}) - {self.get_status_display()}"

class SecurityAlert(models.Model):
    """Model for security alerts that may turn into incidents"""
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=100, default="internal")  # Where the alert came from (e.g., SIEM, IDS, etc.)
    description = models.TextField(default="")
    raw_data = models.JSONField(null=True, blank=True)  # Store raw alert data
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Related incident, if this alert was escalated
    related_incident = models.ForeignKey(
        SecurityIncident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_alerts'
    )
    
    # Who's looking at this alert
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts'
    )
    
    # Alert assessment
    false_positive = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()}) - {self.get_status_display()}"

class SocTask(models.Model):
    """Model for SOC team tasks not directly tied to incidents"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(
        max_length=20,
        choices=[
            ('highest', 'Highest'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium'
    )
    
    # Task assignment and tracking
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tasks'
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Progress
    completion_notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"

class SecurityReport(models.Model):
    """Model for security reports and assessments"""
    title = models.CharField(max_length=200)
    summary = models.TextField(default="")
    content = HTMLField(default="")  # Rich text for full report
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='authored_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Report classification
    REPORT_TYPE_CHOICES = [
        ('incident', 'Incident Report'),
        ('threat', 'Threat Assessment'),
        ('vulnerability', 'Vulnerability Assessment'),
        ('audit', 'Security Audit'),
        ('metrics', 'Security Metrics'),
        ('other', 'Other')
    ]
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='other')
    
    # Related items
    related_incidents = models.ManyToManyField(
        SecurityIncident,
        blank=True,
        related_name='related_reports'
    )
    
    # Report visibility
    VISIBILITY_CHOICES = [
        ('soc_only', 'SOC Team Only'),
        ('management', 'Management'),
        ('all_staff', 'All Staff'),
        ('public', 'Public')
    ]
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='soc_only')
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"

class PlaybookTemplate(models.Model):
    """SOC response playbooks for standardized incident handling"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    steps = HTMLField()  # Rich text for detailed steps
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_playbooks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Categorization
    CATEGORY_CHOICES = [
        ('malware', 'Malware Response'),
        ('phishing', 'Phishing Response'),
        ('data_breach', 'Data Breach'),
        ('ransomware', 'Ransomware'),
        ('ddos', 'DDoS Attack'),
        ('insider_threat', 'Insider Threat'),
        ('other', 'Other')
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

class SecurityMetric(models.Model):
    """Model for tracking security metrics and KPIs"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    current_value = models.FloatField()
    target_value = models.FloatField()
    unit = models.CharField(max_length=50)  # e.g., "days", "percent", "count"
    
    # Tracking
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    
    # Historical data through related MetricDataPoint objects
    
    def __str__(self):
        return f"{self.name}: {self.current_value} {self.unit}"

class MetricDataPoint(models.Model):
    """Historical data points for security metrics"""
    metric = models.ForeignKey(
        SecurityMetric,
        on_delete=models.CASCADE,
        related_name='data_points'
    )
    value = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.metric.name}: {self.value} ({self.recorded_at.strftime('%Y-%m-%d')})"

class Incident(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(default="")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_soc_incidents')  # Changed from 'reported_incidents'
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_soc_incidents')  # Changed from 'assigned_incidents'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class IncidentResponse(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    action_taken = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.incident.title} by {self.responder.username}"
