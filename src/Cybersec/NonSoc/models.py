from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class UserNotification(models.Model):
    """Notifications for users"""
    NOTIFICATION_TYPES = (
        ('course', 'Course'),
        ('security', 'Security'),
        ('achievement', 'Achievement'),
        ('awareness', 'Awareness Module'),
        ('general', 'General'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

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

class SecurityRequest(models.Model):
    """Security requests submitted by non-SOC users"""
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_requests')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

