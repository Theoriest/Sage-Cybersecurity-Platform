from django import forms
from tinymce.widgets import TinyMCE
from .models import (
    SecurityIncident, 
    SecurityAlert,
    SocTask,
    SecurityReport,
    PlaybookTemplate,
    SecurityMetric,
    Incident,
    IncidentResponse
)
from user.models import SOCUser

class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ['title', 'description', 'severity', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class IncidentResponseForm(forms.ModelForm):
    class Meta:
        model = IncidentResponse
        fields = ['content', 'action_taken']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class SecurityIncidentForm(forms.ModelForm):
    """Form for creating and editing security incidents"""
    details = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 20}))
    remediation_steps = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 15}), required=False)
    
    class Meta:
        model = SecurityIncident
        fields = [
            'title', 'description', 'details', 'severity', 'status',
            'assigned_to', 'affected_systems', 'remediation_steps', 'resolution_summary'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'resolution_summary': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter assigned_to field to only include SOC users
        self.fields['assigned_to'].queryset = SOCUser.objects.select_related('user').all()
        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name} ({obj.get_role_display()})"

class SecurityAlertForm(forms.ModelForm):
    """Form for security alerts"""
    class Meta:
        model = SecurityAlert
        fields = [
            'title', 'source', 'description', 'severity', 'status',
            'assigned_to', 'related_incident', 'false_positive', 'notes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter assigned_to field to only include SOC users
        self.fields['assigned_to'].queryset = SOCUser.objects.select_related('user').all()
        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name} ({obj.get_role_display()})"

class SocTaskForm(forms.ModelForm):
    """Form for SOC tasks"""
    class Meta:
        model = SocTask
        fields = [
            'title', 'description', 'status', 'priority',
            'assigned_to', 'due_date', 'completion_notes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'completion_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter assigned_to field to only include SOC users
        self.fields['assigned_to'].queryset = SOCUser.objects.select_related('user').all()
        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name} ({obj.get_role_display()})"

class SecurityReportForm(forms.ModelForm):
    """Form for security reports"""
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
    
    class Meta:
        model = SecurityReport
        fields = [
            'title', 'summary', 'content', 'report_type',
            'related_incidents', 'visibility'
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 4}),
            'related_incidents': forms.CheckboxSelectMultiple(),
        }

class PlaybookTemplateForm(forms.ModelForm):
    """Form for incident response playbooks"""
    steps = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
    
    class Meta:
        model = PlaybookTemplate
        fields = [
            'title', 'description', 'steps', 'category'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class SecurityMetricForm(forms.ModelForm):
    """Form for security metrics"""
    class Meta:
        model = SecurityMetric
        fields = [
            'name', 'description', 'current_value', 'target_value', 'unit'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }