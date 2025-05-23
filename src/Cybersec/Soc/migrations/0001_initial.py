# Generated by Django 5.2 on 2025-04-08 07:49

import django.db.models.deletion
import tinymce.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlaybookTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('steps', tinymce.models.HTMLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(choices=[('malware', 'Malware Response'), ('phishing', 'Phishing Response'), ('data_breach', 'Data Breach'), ('ransomware', 'Ransomware'), ('ddos', 'DDoS Attack'), ('insider_threat', 'Insider Threat'), ('other', 'Other')], max_length=20)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_playbooks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SecurityIncident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('details', tinymce.models.HTMLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('severity', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low'), ('info', 'Informational')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('under_review', 'Under Review'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='new', max_length=20)),
                ('affected_systems', models.TextField()),
                ('remediation_steps', tinymce.models.HTMLField(blank=True, null=True)),
                ('resolution_summary', models.TextField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_incidents', to=settings.AUTH_USER_MODEL)),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reported_incidents', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SecurityAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('source', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('raw_data', models.JSONField(blank=True, null=True)),
                ('severity', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low'), ('info', 'Informational')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('under_review', 'Under Review'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='new', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('false_positive', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_alerts', to=settings.AUTH_USER_MODEL)),
                ('related_incident', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_alerts', to='Soc.securityincident')),
            ],
        ),
        migrations.CreateModel(
            name='SecurityMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('current_value', models.FloatField()),
                ('target_value', models.FloatField()),
                ('unit', models.CharField(max_length=50)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MetricDataPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('metric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_points', to='Soc.securitymetric')),
            ],
        ),
        migrations.CreateModel(
            name='SecurityReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('summary', models.TextField()),
                ('content', tinymce.models.HTMLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report_type', models.CharField(choices=[('incident', 'Incident Report'), ('threat', 'Threat Assessment'), ('vulnerability', 'Vulnerability Assessment'), ('audit', 'Security Audit'), ('metrics', 'Security Metrics'), ('other', 'Other')], max_length=20)),
                ('visibility', models.CharField(choices=[('soc_only', 'SOC Team Only'), ('management', 'Management'), ('all_staff', 'All Staff'), ('public', 'Public')], default='soc_only', max_length=20)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='authored_reports', to=settings.AUTH_USER_MODEL)),
                ('related_incidents', models.ManyToManyField(blank=True, related_name='related_reports', to='Soc.securityincident')),
            ],
        ),
        migrations.CreateModel(
            name='SocTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('under_review', 'Under Review'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='new', max_length=20)),
                ('priority', models.CharField(choices=[('highest', 'Highest'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='medium', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('completion_notes', models.TextField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_tasks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
