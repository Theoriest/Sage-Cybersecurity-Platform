from django import forms
from .models import (
    Course, 
    Module, 
    Chapter, 
    Question, 
    Choice, 
    CourseEvaluation,
    CourseCreationSession,
    DocumentContext
)
from tinymce.widgets import TinyMCE

class CourseForm(forms.ModelForm):
    """Form for creating and editing courses"""
    class Meta:
        model = Course
        fields = ['title', 'description', 'course_type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ModuleForm(forms.ModelForm):
    """Form for creating and editing modules"""
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ChapterForm(forms.ModelForm):
    """Form for creating and editing chapters"""
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
    
    class Meta:
        model = Chapter
        fields = ['title', 'content', 'order', 'is_summary']

class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions"""
    class Meta:
        model = Question
        fields = ['question_text']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
        }

class ChoiceForm(forms.ModelForm):
    """Form for creating and editing choices"""
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']

class CourseInitialPromptForm(forms.Form):
    """Form for the initial prompt for course creation"""
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the course you want to create...'}),
        label="Course Description"
    )
    
    # Replace the FileField with a standard field for the file input
    documents = forms.FileField(
        required=False,
        label="Upload Context Documents (Optional)",
        help_text="You can select multiple files"
    )

class CoursePromptForm(forms.Form):
    """Form for subsequent prompts during course creation"""
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Your Response"
    )

class CourseEvaluationForm(forms.ModelForm):
    """Form for evaluating completed courses"""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label="How satisfied were you with this course?"
    )
    
    class Meta:
        model = CourseEvaluation
        fields = ['rating', 'feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Please share your feedback about the course (optional)'
            }),
        }

class QuizForm(forms.Form):
    """Dynamic form for chapter quizzes"""
    def __init__(self, chapter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add a field for each question in the chapter
        for question in chapter.questions.all():
            choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                label=question.question_text,
                choices=choices,
                widget=forms.RadioSelect,
                required=True
            )
