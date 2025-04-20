from django.db.models.signals import post_save
from django.dispatch import receiver
from Courses.models import Enrollment
from NonSoc.models import UserNotification
from .models import AwarenessModule

@receiver(post_save, sender=Enrollment)
def notify_user_about_awareness_module(sender, instance, created, **kwargs):
    """Create notification for awareness module when course is completed"""
    # Only proceed if the enrollment is marked as completed
    if not instance.completed:
        return
    
    # Check if there's an awareness module for this course
    try:
        module = AwarenessModule.objects.get(course=instance.course)
    except AwarenessModule.DoesNotExist:
        # No awareness module exists for this course
        return
    
    # Check if user has already completed this module
    if instance.user.awareness_attempts.filter(module=module, passed=True).exists():
        # User already passed this module
        return
        
    # Create notification for the user
    UserNotification.objects.create(
        user=instance.user,
        title="Security Awareness Check",
        message=f"Complete the awareness module for '{instance.course.title}' to earn {module.get_point_value()} points!",
        notification_type='awareness',
        link=f"/awareness/module/{module.id}/",
        is_read=False
    )
