from __future__ import annotations

import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import get_valid_filename

from accounts.models import Area


def ticket_attachment_upload_to(instance: "TicketAttachment", filename: str) -> str:
    safe_name = get_valid_filename(os.path.basename(filename))
    return f"tickets/{instance.ticket_id or 'tmp'}/{uuid.uuid4().hex}_{safe_name}"


class Ticket(models.Model):
    class Status(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_CURSO = "en_curso", "En curso"
        ESPERANDO_CONFIRMACION = "esperando_confirmacion", "Esperando confirmación"
        RESUELTO = "resuelto", "Resuelto"
        CERRADO = "cerrado", "Cerrado"

    class Priority(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"

    subject = models.CharField(max_length=200)
    description = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="tickets")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDIENTE)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIA)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tickets")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"#{self.pk} - {self.subject}"


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_comments")
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comentario {self.pk} en ticket {self.ticket_id}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, null=True, blank=True, on_delete=models.CASCADE, related_name="attachments")
    comment = models.ForeignKey(TicketComment, null=True, blank=True, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=ticket_attachment_upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_attachments")

    class Meta:
        ordering = ["uploaded_at"]

    def clean(self) -> None:
        if bool(self.ticket) == bool(self.comment):
            raise ValidationError("El adjunto debe pertenecer al ticket o al comentario, no a ambos.")

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if self.file and self.file.size > max_size:
            raise ValidationError(f"El archivo excede {settings.MAX_UPLOAD_SIZE_MB} MB")

    def save(self, *args, **kwargs):
        if self.file:
            self.file.name = get_valid_filename(os.path.basename(self.file.name))
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Adjunto {self.pk}"
