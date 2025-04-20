from django.conf import settings as django_settings

def settings(request):
    """Make settings available to all templates."""
    return {'settings': django_settings}
