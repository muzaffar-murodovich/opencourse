from django import template

register = template.Library()

@register.filter
def duration(seconds):
    """Soniyani '1 soat 23 daqiqa' formatiga o'tkazadi."""
    seconds = int(seconds or 0)
    if seconds <= 0:
        return "0 daqiqa"
    total_minutes = seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours and minutes:
        return f"{hours} soat {minutes} daqiqa"
    if hours:
        return f"{hours} soat"
    return f"{minutes} daqiqa"

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))