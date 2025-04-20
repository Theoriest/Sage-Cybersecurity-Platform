from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from django.core.validators import RegexValidator, EmailValidator

# Define choices for departments and roles
DEPARTMENT_CHOICES = [
    ('HR', 'Human Resources'),
    ('IT', 'Information Technology'),
    ('FIN', 'Finance'),
    ('MKT', 'Marketing'),
    ('OPS', 'Operations'),
    ('SEC', 'Security'),
    ('DEV', 'Development'),
    ('OTHER', 'Other'),
]

ROLE_CHOICES = [
    ('analyst', 'SOC Analyst'),
    ('engineer', 'SOC Engineer'),
    ('manager', 'SOC Manager'),
    ('lead', 'SOC Lead'),
    ('architect', 'Security Architect'),
    ('researcher', 'Security Researcher'),
    ('admin', 'SOC Administrator'),
]

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        if not username:
            raise ValueError("The Username field is required")
        if not password:
            raise ValueError("The Password field is required")
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_soc_user(self, username, email, first_name, last_name, unique_identifier, role, password=None):
        extra_fields = {
            'user_type': 'soc',
        }
        user = self.create_user(username, email, first_name, last_name, password, **extra_fields)
        SOCUser.objects.create(user=user, unique_identifier=unique_identifier, role=role)
        return user

    def create_non_soc_user(self, username, email, first_name, last_name, department, password=None):
        extra_fields = {
            'user_type': 'non_soc',
        }
        user = self.create_user(username, email, first_name, last_name, password, **extra_fields)
        NonSOCUser.objects.create(user=user, department=department)
        return user

    def create_superuser(self, username, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'soc')
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)

        user = self.create_user(username, email, first_name, last_name, password, **extra_fields)
        SOCUser.objects.create(user=user, unique_identifier=f"ADMIN-{username.upper()}", role='admin')
        return user

# Base User Model
class CustomUser(AbstractBaseUser):
    USER_TYPE_CHOICES = (
        ('soc', 'SOC User'),
        ('non_soc', 'Non-SOC User'),
    )

    username = models.CharField(
        max_length=150, 
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+$', 'Enter a valid username.')]
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()]
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='non_soc')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    last_password_change = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def requires_password_change(self):
        # Logic to determine if password change is required
        # For example, if password is older than 90 days
        if not self.last_password_change:
            return True
        return False

# SOC User Model
class SOCUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='soc_profile')
    unique_identifier = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='analyst')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.profile_picture:
            self.profile_picture = self.generate_profile_picture()
        super().save(*args, **kwargs)

    def generate_profile_picture(self):
        initials = f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        image = Image.new('RGB', (200, 200), color=(41, 128, 185))  # Professional blue for SOC
        draw = ImageDraw.Draw(image)

        # Use a built-in font
        font = ImageFont.load_default()

        # Calculate text dimensions
        text_bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Center the text in the image
        text_x = (200 - text_width) / 2
        text_y = (200 - text_height) / 2
        draw.text((text_x, text_y), initials, fill=(255, 255, 255), font=font)

        # Save the image
        image_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', f"{self.user.username}_soc_profile.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)

        return f"profile_pictures/{self.user.username}_soc_profile.png"

    def __str__(self):
        return f"{self.user.full_name} ({self.get_role_display()})"

# Non-SOC User Model
class NonSOCUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='non_soc_profile')
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='OTHER')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    completed_trainings = models.IntegerField(default=0)
    security_awareness_level = models.IntegerField(default=1)  # 1-5 scale
    
    def save(self, *args, **kwargs):
        if not self.profile_picture:
            self.profile_picture = self.generate_profile_picture()
        super().save(*args, **kwargs)

    def generate_profile_picture(self):
        initials = f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        image = Image.new('RGB', (200, 200), color=(46, 204, 113))  # Green for non-SOC
        draw = ImageDraw.Draw(image)

        # Use a built-in font
        font = ImageFont.load_default()

        # Calculate text dimensions
        text_bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Center the text in the image
        text_x = (200 - text_width) / 2
        text_y = (200 - text_height) / 2
        draw.text((text_x, text_y), initials, fill=(255, 255, 255), font=font)

        # Save the image
        image_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', f"{self.user.username}_nonsoc_profile.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)

        return f"profile_pictures/{self.user.username}_nonsoc_profile.png"

    def __str__(self):
        return f"{self.user.full_name} ({self.get_department_display()})"
    
    def get_awareness_level_display(self):
        levels = {
            1: "Beginner",
            2: "Basic",
            3: "Intermediate",
            4: "Advanced",
            5: "Expert"
        }
        return levels.get(self.security_awareness_level, "Unknown")
