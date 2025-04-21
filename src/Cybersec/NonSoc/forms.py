from django import forms
from .models import SecurityRequest

class SecurityRequestForm(forms.ModelForm):
    class Meta:
        model = SecurityRequest
        fields = ['title', 'description', 'priority', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
