from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser, SOCUser, NonSOCUser

User = get_user_model()

class SOCUserSignupForm(forms.ModelForm):
    unique_identifier = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=SOCUser._meta.get_field('role').choices, 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match")
        return cleaned_data

    def save(self, admin_user=None, commit=True):
        user = super().save(commit=False)
        user.user_type = 'soc'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            SOCUser.objects.create(
                user=user,
                unique_identifier=self.cleaned_data['unique_identifier'],
                role=self.cleaned_data['role']
            )
        return user

class SOCUserLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), 
        required=True
    )

class NonSOCUserSignupForm(forms.ModelForm):
    department = forms.ChoiceField(
        choices=NonSOCUser._meta.get_field('department').choices, 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    job_title = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'non_soc'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            NonSOCUser.objects.create(
                user=user,
                department=self.cleaned_data['department'],
                job_title=self.cleaned_data.get('job_title')
            )
        return user

class NonSOCUserLoginForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), 
        required=True
    )

class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        required=False, 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = kwargs.get('instance')
        
        # Add SOC-specific or NonSOC-specific fields
        if user and user.user_type == 'soc' and hasattr(user, 'soc_profile'):
            self.fields['role'] = forms.ChoiceField(
                choices=SOCUser._meta.get_field('role').choices,
                initial=user.soc_profile.role,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            self.fields['bio'] = forms.CharField(
                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                initial=user.soc_profile.bio,
                required=False
            )
            self.fields['certifications'] = forms.CharField(
                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                initial=user.soc_profile.certifications,
                required=False
            )
            
        elif user and user.user_type == 'non_soc' and hasattr(user, 'non_soc_profile'):
            self.fields['department'] = forms.ChoiceField(
                choices=NonSOCUser._meta.get_field('department').choices,
                initial=user.non_soc_profile.department,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            self.fields['job_title'] = forms.CharField(
                max_length=100,
                initial=user.non_soc_profile.job_title,
                required=False,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        
        if hasattr(user, 'soc_profile'):
            soc_profile = user.soc_profile
            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                soc_profile.profile_picture = self.cleaned_data['profile_picture']
            if 'role' in self.cleaned_data:
                soc_profile.role = self.cleaned_data['role']
            if 'bio' in self.cleaned_data:
                soc_profile.bio = self.cleaned_data['bio']
            if 'certifications' in self.cleaned_data:
                soc_profile.certifications = self.cleaned_data['certifications']
                
            if commit:
                soc_profile.save()
                
        elif hasattr(user, 'non_soc_profile'):
            non_soc_profile = user.non_soc_profile
            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                non_soc_profile.profile_picture = self.cleaned_data['profile_picture']
            if 'department' in self.cleaned_data:
                non_soc_profile.department = self.cleaned_data['department']
            if 'job_title' in self.cleaned_data:
                non_soc_profile.job_title = self.cleaned_data['job_title']
                
            if commit:
                non_soc_profile.save()
                
        if commit:
            user.save()
            
        return user

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})