from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def currency(value):
    """Format en FCFA avec séparation des milliers."""
    try:
        return f"{int(value):,} FCFA".replace(',', ' ')
    except (ValueError, TypeError):
        return value
