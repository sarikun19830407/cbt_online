from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)




@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, {'huruf': None, 'nilai': 0, 'benar': False})

@register.filter(name='percentage')
def percentage(value, total):
    try:
        if value and total:
            # Untuk DurationField (value adalah timedelta)
            if hasattr(value, 'total_seconds'):
                seconds = value.total_seconds()
                total_seconds = total * 60  # Convert menit ke detik
                return (seconds / total_seconds) * 100
            # Untuk numeric biasa
            return (float(value) / float(total)) * 100
        return 0
    except (ValueError, ZeroDivisionError):
        return 0
    

@register.filter
def percentage(sisa_waktu, durasi_menit):
    try:
        total_seconds = durasi_menit * 60
        remaining = sisa_waktu.total_seconds()
        result = (remaining / total_seconds) * 100
        return round(result, 1)
    except:
        return 0