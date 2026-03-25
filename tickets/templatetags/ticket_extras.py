from django import template

register = template.Library()


@register.filter
def status_badge(status):
    mapping = {
        "pendiente": "secondary",
        "en_curso": "primary",
        "esperando_confirmacion": "warning",
        "resuelto": "success",
        "cerrado": "dark",
    }
    return mapping.get(status, "secondary")


@register.filter
def priority_badge(priority):
    mapping = {"baja": "success", "media": "warning", "alta": "danger"}
    return mapping.get(priority, "secondary")
