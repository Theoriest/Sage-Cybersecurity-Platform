from django.contrib import admin
from .models import (
    Course, 
    Module, 
    Chapter, 
    Question, 
    Choice, 
    Enrollment, 
    Progress,
    CourseEvaluation,
    CourseCreationSession,
    SessionMessage,
    DocumentContext
)

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_type', 'created_by', 'created_at')
    list_filter = ('course_type', 'created_at')
    search_fields = ('title', 'description')
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description')
    inlines = [ChapterInline]

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'is_summary')
    list_filter = ('module', 'is_summary')
    search_fields = ('title', 'content')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'chapter')
    list_filter = ('chapter',)
    search_fields = ('question_text',)
    inlines = [ChoiceInline]

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('choice_text', 'question', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('choice_text',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'date_enrolled', 'completed']
    list_filter = ['completed', 'date_enrolled']
    search_fields = ['user__username', 'course__title']

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'chapter', 'completed')
    list_filter = ('completed',)
    search_fields = ('enrollment__user__username', 'chapter__title')

@admin.register(CourseEvaluation)
class CourseEvaluationAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'rating', 'submitted_date')
    list_filter = ('rating',)
    search_fields = ('enrollment__user__username', 'enrollment__course__title', 'feedback')

@admin.register(CourseCreationSession)
class CourseCreationSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'initial_prompt')

@admin.register(SessionMessage)
class SessionMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'is_user', 'timestamp')
    list_filter = ('is_user',)
    search_fields = ('content',)

@admin.register(DocumentContext)
class DocumentContextAdmin(admin.ModelAdmin):
    list_display = ('session', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('content_text',)
