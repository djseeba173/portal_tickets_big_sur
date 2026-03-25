from django.conf import settings
from django.db import models


class Area(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AgentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile")
    areas = models.ManyToManyField(Area, blank=True, related_name="agents")

    def __str__(self) -> str:
        return f"Perfil agente: {self.user.username}"
