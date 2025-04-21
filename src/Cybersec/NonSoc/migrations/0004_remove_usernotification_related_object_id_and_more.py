# Generated manually to fix migration issues

from django.db import migrations, models

def check_and_remove_columns(apps, schema_editor):
    """Check if columns exist and remove them if they do"""
    # Check if columns exist before trying to remove them
    cursor = schema_editor.connection.cursor()
    
    # Check for related_object_id column
    cursor.execute(
        "SELECT COUNT(*) FROM pragma_table_info('NonSoc_usernotification') WHERE name='related_object_id';"
    )
    if cursor.fetchone()[0] > 0:
        # Column exists, we can remove it
        cursor.execute(
            "ALTER TABLE NonSoc_usernotification DROP COLUMN related_object_id;"
        )
    
    # Check for related_object_type column
    cursor.execute(
        "SELECT COUNT(*) FROM pragma_table_info('NonSoc_usernotification') WHERE name='related_object_type';"
    )
    if cursor.fetchone()[0] > 0:
        # Column exists, we can remove it
        cursor.execute(
            "ALTER TABLE NonSoc_usernotification DROP COLUMN related_object_type;"
        )

def reverse_migration(apps, schema_editor):
    """Reverse migration - add columns back if needed"""
    # This is a no-op since we're removing columns
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('NonSoc', '0003_securityrequestresponse'),
    ]

    operations = [
        # Use RunPython with proper callable functions
        migrations.RunPython(
            check_and_remove_columns,
            reverse_migration
        ),
        
        # Add notification_type field if it doesn't exist already
        migrations.AddField(
            model_name='usernotification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('system', 'System'), 
                    ('alert', 'Alert'), 
                    ('request_update', 'Request Update'), 
                    ('request_response', 'Request Response')
                ],
                default='system',
                max_length=20
            ),
        ),
    ]
