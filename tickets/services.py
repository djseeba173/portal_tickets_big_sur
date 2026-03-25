from django.conf import settings
from django.core.mail import send_mail

from accounts.permissions import is_agent


def _emails_for_agents(ticket):
    emails = set()
    for profile in ticket.area.agents.select_related("user"):
        if profile.user.email:
            emails.add(profile.user.email)
    return sorted(emails)


def send_ticket_created_emails(ticket):
    recipients = _emails_for_agents(ticket)
    if recipients:
        send_mail(
            subject=f"[HelpDesk] Nuevo ticket #{ticket.pk} - {ticket.subject}",
            message=f"Se creó el ticket #{ticket.pk} en el área {ticket.area.name}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
    if ticket.created_by.email:
        send_mail(
            subject=f"[HelpDesk] Confirmación de ticket #{ticket.pk}",
            message=f"Tu ticket '{ticket.subject}' fue creado correctamente.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.created_by.email],
            fail_silently=True,
        )


def send_comment_email(ticket, author, is_internal=False):
    if is_internal:
        return
    if is_agent(author):
        if ticket.created_by.email:
            send_mail(
                subject=f"[HelpDesk] Respuesta en ticket #{ticket.pk}",
                message=f"Un agente respondió tu ticket '{ticket.subject}'.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[ticket.created_by.email],
                fail_silently=True,
            )
    else:
        recipients = _emails_for_agents(ticket)
        if ticket.assigned_to and ticket.assigned_to.email:
            recipients = sorted(set(recipients + [ticket.assigned_to.email]))
        if recipients:
            send_mail(
                subject=f"[HelpDesk] Usuario respondió ticket #{ticket.pk}",
                message=f"El usuario agregó un comentario al ticket '{ticket.subject}'.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,
            )


def send_status_changed_email(ticket):
    if ticket.created_by.email:
        send_mail(
            subject=f"[HelpDesk] Cambio de estado en ticket #{ticket.pk}",
            message=f"El estado de tu ticket '{ticket.subject}' cambió a {ticket.get_status_display()}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.created_by.email],
            fail_silently=True,
        )
