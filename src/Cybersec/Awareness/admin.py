from django.contrib import admin
from .models import AwarenessModule, Question, Answer, ModuleAttempt, UserResponse

@admin.register(AwarenessModule)
class AwarenessModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'difficulty', 'points', 'created_at')
    list_filter = ('difficulty', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    date_hierarchy = 'created_at'

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'module', 'question_type', 'course_module_number')
    list_filter = ('question_type', 'module')
    inlines = [AnswerInline]

@admin.register(ModuleAttempt)
class ModuleAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'score', 'passed', 'attempt_date')
    list_filter = ('passed', 'attempt_date')
    date_hierarchy = 'attempt_date'

@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct')
    list_filter = ('is_correct',)
