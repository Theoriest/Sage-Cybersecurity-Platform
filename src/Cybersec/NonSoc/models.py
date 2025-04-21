from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class UserNotification(models.Model):
    """Notifications for users"""
    NOTIFICATION_TYPE_CHOICES = (
        ('system', 'System'),
        ('alert', 'Alert'),
        ('request_update', 'Request Update'),
        ('request_response', 'Request Response'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPE_CHOICES,
        default='system'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ArticleRead(models.Model):
    """Track which articles users have read"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    article = models.ForeignKey('Articles.Article', on_delete=models.CASCADE, related_name='reads')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'article')
        
    def __str__(self):
        return f"{self.user.username} read {self.article.title}"

class UserAchievement(models.Model):
    """Track user achievements in security awareness"""
    ACHIEVEMENT_TYPES = [
        ('course_complete', 'Completed Course'),
        ('streak', 'Login Streak'),
        ('perfect_score', 'Perfect Quiz Score'),
        ('security_level', 'Security Level Advancement'),
        ('department_leader', 'Department Leader'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_earned = models.DateTimeField(auto_now_add=True)
    icon = models.CharField(max_length=50, default='trophy')  # CSS class or icon name
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class SecurityAwareness(models.Model):
    """Security awareness content for non-SOC users"""
    title = models.CharField(max_length=200)
    content = models.TextField(default='')
    points = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    users_completed = models.ManyToManyField(User, related_name='completed_awareness', blank=True)
    
    def __str__(self):
        return self.title

class SecurityRequest(models.Model):
    """Security requests submitted by non-SOC users"""
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('pending_info', 'Pending Info'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    CATEGORY_CHOICES = (
        ('access', 'Access Request'),
        ('incident', 'Security Incident'),
        ('vulnerability', 'Vulnerability Report'),
        ('question', 'General Question'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_requests')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class SecurityRequestResponse(models.Model):
    """Responses to security requests from SOC team members"""
    security_request = models.ForeignKey(SecurityRequest, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_responses')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.security_request.title} by {self.responder.username}"

