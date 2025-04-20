from django import template

register = template.Library()

@register.filter
def has_question_for_module(questions, module_index):
    """Check if any questions exist for a specific module index"""
    return questions.filter(course_module_number=module_index).exists()

@register.filter
def get_minutes(seconds):
    """Get minutes part from seconds"""
    if seconds is None:
        return 0
    return seconds // 60

@register.filter
def get_seconds(seconds):
    """Get remaining seconds after minutes"""
    if seconds is None:
        return 0
    return seconds % 60

@register.filter(name='div')
def div(value, arg):
    """Divides the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
