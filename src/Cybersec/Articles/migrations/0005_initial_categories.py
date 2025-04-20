from django.db import migrations
from django.utils.text import slugify

def create_default_categories(apps, schema_editor):
    # Get the Category model
    Category = apps.get_model('Articles', 'Category')
    
    # Define default security categories
    default_categories = [
        'Network Security',
        'Application Security',
        'Cloud Security',
        'Endpoint Protection',
        'Security Best Practices',
        'Incident Response',
        'Threat Intelligence',
        'Compliance',
        'Security Awareness',
        'Data Protection'
    ]
    
    # Create categories
    for category_name in default_categories:
        Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': slugify(category_name)}
        )

def remove_default_categories(apps, schema_editor):
    # Get the Category model
    Category = apps.get_model('Articles', 'Category')
    
    # Define default security categories
    default_categories = [
        'Network Security',
        'Application Security',
        'Cloud Security',
        'Endpoint Protection',
        'Security Best Practices',
        'Incident Response',
        'Threat Intelligence',
        'Compliance',
        'Security Awareness',
        'Data Protection'
    ]
    
    # Remove categories
    Category.objects.filter(name__in=default_categories).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('Articles', '0004_article_visibility'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ]
