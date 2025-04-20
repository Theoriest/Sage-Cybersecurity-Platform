from django.contrib import admin
from .models import (
    SecurityIncident, 
    SecurityAlert,
    SocTask,
    SecurityReport,
    PlaybookTemplate,
    SecurityMetric,
    MetricDataPoint
)

@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'status', 'assigned_to', 'created_at')
    list_filter = ('severity', 'status')
    search_fields = ('title', 'description', 'affected_systems')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'details', 'severity', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'reported_by')
        }),
        ('Incident Details', {
            'fields': ('affected_systems', 'remediation_steps', 'resolution_summary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'severity', 'status', 'false_positive', 'created_at')
    list_filter = ('severity', 'status', 'false_positive', 'source')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'source', 'description', 'severity', 'status')
        }),
        ('Assessment', {
            'fields': ('assigned_to', 'false_positive', 'notes')
        }),
        ('Related Data', {
            'fields': ('raw_data', 'related_incident')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(SocTask)
class SocTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'status', 'assigned_to', 'due_date')
    list_filter = ('priority', 'status')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by', 'due_date')
        }),
        ('Progress', {
            'fields': ('completion_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(SecurityReport)
class SecurityReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'author', 'visibility', 'created_at')
    list_filter = ('report_type', 'visibility')
    search_fields = ('title', 'summary')
    date_hierarchy = 'created_at'
    filter_horizontal = ('related_incidents',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PlaybookTemplate)
class PlaybookTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_by', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

class MetricDataPointInline(admin.TabularInline):
    model = MetricDataPoint
    extra = 1

@admin.register(SecurityMetric)
class SecurityMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_value', 'target_value', 'unit', 'last_updated')
    search_fields = ('name', 'description')
    inlines = [MetricDataPointInline]
    readonly_fields = ('last_updated',)

@admin.register(MetricDataPoint)
class MetricDataPointAdmin(admin.ModelAdmin):
    list_display = ('metric', 'value', 'recorded_at')
    list_filter = ('metric',)
    search_fields = ('notes',)
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)
