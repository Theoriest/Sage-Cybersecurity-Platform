# Generated by Django 5.2 on 2025-04-09 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Articles', '0003_category_article_slug_article_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='visibility',
            field=models.CharField(choices=[('public', 'Public'), ('soc', 'SOC Only'), ('non_soc', 'Non-SOC Only'), ('private', 'Private')], default='public', max_length=10),
        ),
    ]
