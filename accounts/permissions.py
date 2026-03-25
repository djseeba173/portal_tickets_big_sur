from django.contrib.auth.models import User


def is_agent(user: User) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="Agentes").exists()


def is_end_user(user: User) -> bool:
    if not user.is_authenticated:
        return False
    return user.groups.filter(name="Usuarios").exists() and not is_agent(user)
