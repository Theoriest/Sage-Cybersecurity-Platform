from django import forms
from .models import SecurityRequest

class SecurityRequestForm(forms.ModelForm):
    class Meta:
        model = SecurityRequest
        fields = ['title', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
