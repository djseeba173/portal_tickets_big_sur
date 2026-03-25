from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_default_groups(sender, **kwargs):
    Group.objects.get_or_create(name="Usuarios")
    Group.objects.get_or_create(name="Agentes")

    # Evita warning de import no usado cuando app registry carga señales.
    get_user_model()
