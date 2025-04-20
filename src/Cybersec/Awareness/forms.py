from django import forms
from .models import AwarenessModule, Question, Answer
from Courses.models import Course

class AwarenessModuleForm(forms.ModelForm):
    """Form for creating and editing awareness modules"""
    class Meta:
        model = AwarenessModule
        fields = ['title', 'description', 'course', 'points', 'difficulty']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit courses to those created by this user and those without an existing awareness module
        if user:
            if self.instance.pk:
                # If editing, include the current course
                self.fields['course'].queryset = Course.objects.filter(
                    created_by=user
                )
            else:
                # If creating new, only show courses without awareness modules
                existing_modules = AwarenessModule.objects.values_list('course_id', flat=True)
                self.fields['course'].queryset = Course.objects.filter(
                    created_by=user
                ).exclude(id__in=existing_modules)

class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions"""
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'course_module_number', 'explanation']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'course_module_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AnswerForm(forms.ModelForm):
    """Form for creating and editing answers"""
    class Meta:
        model = Answer
        fields = ['text', 'is_correct', 'explanation']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class AIQuestionGenerationForm(forms.Form):
    """Form for generating questions with AI"""
    use_ai = forms.BooleanField(
        label="Use AI to suggest questions",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    additional_context = forms.CharField(
        label="Additional context for AI (optional)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
