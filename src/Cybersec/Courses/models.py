from django.db import models
from django.conf import settings
from tinymce.models import HTMLField
from django.contrib.auth import get_user_model

User = get_user_model()

# Course types
COURSE_TYPE_CHOICES = [
    ('awareness', 'Security Awareness'),
    ('advanced', 'Advanced Security'),
]

class Course(models.Model):
    """Model for security courses"""
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(default="")
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES, default='awareness')
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_courses'
    )
    
    def __str__(self):
        return self.title
    
    @property
    def total_modules(self):
        return self.modules.count()
    
    @property
    def total_chapters(self):
        chapter_count = 0
        for module in self.modules.all():
            chapter_count += module.chapters.count()
        return chapter_count

class Module(models.Model):
    """Model for course modules"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(default="")
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Chapter(models.Model):
    """Model for module chapters"""
    title = models.CharField(max_length=200)
    content = models.TextField(default="")  # Assuming HTMLField is a TextField
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE,
        related_name='chapters'
    )
    order = models.PositiveIntegerField(default=0)
    is_summary = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.course.title} - {self.module.title} - {self.title}"

class Question(models.Model):
    """Model for chapter evaluation questions"""
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField(default="")
    
    def __str__(self):
        return f"Question for {self.chapter.title}"

class Choice(models.Model):
    """Model for question choices"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.choice_text

class Enrollment(models.Model):
    """Model to track user enrollments in courses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    progress_value = models.PositiveIntegerField(default=0)  # Renamed from 'progress' to 'progress_value'
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class CompletedModule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    date_completed = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'module')
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title}"

class Progress(models.Model):
    """Model to track user progress in chapters"""
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['enrollment', 'chapter']
    
    def __str__(self):
        return f"{self.enrollment.user.username} - {self.chapter.title}"

class CourseEvaluation(models.Model):
    """Model for course evaluation by users"""
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='evaluation'
    )
    rating = models.PositiveIntegerField()  # 1-5 rating
    feedback = models.TextField(blank=True, null=True)
    submitted_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.enrollment.user.username}'s evaluation of {self.enrollment.course.title}"

class CourseCreationSession(models.Model):
    """Model to track course creation sessions with AI"""
    STATUS_CHOICES = [
        ('title_modules', 'Deciding Course Title and Modules'),
        ('chapters', 'Defining Chapters per Module'),
        ('content', 'Generating Chapter Content'),
        ('completed', 'Course Creation Completed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_creation_sessions'
    )
    initial_prompt = models.TextField(default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='title_modules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    course = models.OneToOneField(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='creation_session'
    )
    
    def __str__(self):
        return f"Course creation by {self.user.username} ({self.get_status_display()})"

class SessionMessage(models.Model):
    """Model for messages in a course creation session"""
    session = models.ForeignKey(
        CourseCreationSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField(default="")
    is_user = models.BooleanField(default=False)  # False for AI messages, True for user messages
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message by {'User' if self.is_user else 'AI'} at {self.timestamp}"

class DocumentContext(models.Model):
    """Model for storing documents used as context for course creation"""
    session = models.ForeignKey(
        CourseCreationSession,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.FileField(upload_to='course_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content_text = models.TextField(null=True, blank=True)  # Extracted text content
    
    def __str__(self):
        return f"Document for {self.session}"
