from django.db import models
from django.conf import settings
from Courses.models import Course

User = settings.AUTH_USER_MODEL

class AwarenessModule(models.Model):
    """Main model for security awareness modules linked to courses"""
    DIFFICULTY_CHOICES = (
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='awareness_module')
    points = models.PositiveIntegerField(default=10, help_text="Base points awarded for completion")
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY_CHOICES, default='basic')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_modules')
    
    def __str__(self):
        return f"{self.title} ({self.course.title})"
    
    def get_point_value(self):
        """Calculate point value based on difficulty"""
        difficulty_multipliers = {
            'basic': 1.0,
            'intermediate': 1.5,
            'advanced': 2.0,
        }
        return int(self.points * difficulty_multipliers.get(self.difficulty, 1.0))
    
    @property
    def question_count(self):
        return self.questions.count()

class Question(models.Model):
    """Model for questions in awareness modules"""
    QUESTION_TYPES = (
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
    )
    
    module = models.ForeignKey(AwarenessModule, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=8, choices=QUESTION_TYPES, default='single')
    course_module_number = models.PositiveSmallIntegerField(help_text="Associated module number in the course", blank=True, null=True)
    explanation = models.TextField(help_text="Explanation shown during review", blank=True)
    
    def __str__(self):
        return f"Question for {self.module.title} - {self.text[:30]}..."
    
    def is_multiple_choice(self):
        return self.question_type == 'multiple'

class Answer(models.Model):
    """Model for answers to questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True, help_text="Specific explanation for this answer choice")
    
    def __str__(self):
        return f"Answer for {self.question_id}: {self.text[:30]}... ({'Correct' if self.is_correct else 'Incorrect'})"

class ModuleAttempt(models.Model):
    """Tracks user attempts at awareness modules"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='awareness_attempts')
    module = models.ForeignKey(AwarenessModule, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)
    attempt_date = models.DateTimeField(auto_now_add=True)
    time_taken = models.PositiveIntegerField(help_text='Time taken in seconds', blank=True, null=True)
    questions_seen = models.ManyToManyField(Question, blank=True, related_name='seen_in_attempts')
    
    class Meta:
        ordering = ['-attempt_date']
    
    def __str__(self):
        return f"{self.user.username}'s attempt at {self.module.title} - {'Passed' if self.passed else 'Failed'}"

class UserResponse(models.Model):
    """Records user responses to questions during module attempts"""
    attempt = models.ForeignKey(ModuleAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, related_name='user_selections')
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Response to question {self.question_id} in attempt {self.attempt_id}"
