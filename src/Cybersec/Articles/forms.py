from django import forms
from .models import Article, Comment
from tinymce.widgets import TinyMCE

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'description', 'content', 'categories', 'status', 'visibility']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief summary of the article'}),
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }