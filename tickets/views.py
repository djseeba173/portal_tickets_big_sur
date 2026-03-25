from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import is_agent

from .forms import TicketCommentForm, TicketCreateForm, TicketUpdateForm
from .models import Ticket, TicketAttachment, TicketComment
from .permissions import can_manage_ticket, can_view_ticket
from .services import send_comment_email, send_status_changed_email, send_ticket_created_emails


def _get_ticket_or_404_for_user(user, pk: int) -> Ticket:
    ticket = get_object_or_404(Ticket.objects.select_related("area", "created_by", "assigned_to"), pk=pk)
    if not can_view_ticket(user, ticket):
        raise Http404("No tienes permisos para ver este ticket")
    return ticket


@login_required
def user_dashboard(request):
    if is_agent(request.user) or request.user.is_superuser:
        return redirect("tickets:agent_dashboard")
    tickets = Ticket.objects.filter(created_by=request.user).select_related("area", "assigned_to")
    return render(request, "tickets/user_dashboard.html", {"tickets": tickets})


@login_required
def agent_dashboard(request):
    if not (is_agent(request.user) or request.user.is_superuser):
        return redirect("tickets:user_dashboard")

    tickets = Ticket.objects.select_related("area", "created_by", "assigned_to")
    if not request.user.is_superuser:
        areas = request.user.agent_profile.areas.all()
        tickets = tickets.filter(area__in=areas)

    status = request.GET.get("status")
    area = request.GET.get("area")
    priority = request.GET.get("priority")
    if status:
        tickets = tickets.filter(status=status)
    if area:
        tickets = tickets.filter(area_id=area)
    if priority:
        tickets = tickets.filter(priority=priority)

    return render(request, "tickets/agent_dashboard.html", {"tickets": tickets, "status": status, "area": area, "priority": priority, "status_choices": Ticket.Status.choices, "priority_choices": Ticket.Priority.choices})


@login_required
def ticket_create(request):
    if is_agent(request.user) or request.user.is_superuser:
        messages.info(request, "Los agentes también pueden crear tickets como usuarios.")
    if request.method == "POST":
        form = TicketCreateForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            for file in request.FILES.getlist("attachments"):
                TicketAttachment.objects.create(ticket=ticket, file=file, uploaded_by=request.user)
            send_ticket_created_emails(ticket)
            messages.success(request, f"Ticket #{ticket.pk} creado correctamente")
            return redirect("tickets:ticket_detail", pk=ticket.pk)
    else:
        form = TicketCreateForm()
    return render(request, "tickets/ticket_form.html", {"form": form})


@login_required
def ticket_detail(request, pk):
    ticket = _get_ticket_or_404_for_user(request.user, pk)
    agent = is_agent(request.user) or request.user.is_superuser
    comments = ticket.comments.select_related("author").prefetch_related("attachments")
    if not agent:
        comments = comments.filter(is_internal=False)

    if request.method == "POST" and "add_comment" in request.POST:
        if ticket.status == Ticket.Status.CERRADO:
            messages.error(request, "No se puede responder un ticket cerrado.")
            return redirect("tickets:ticket_detail", pk=ticket.pk)

        form = TicketCommentForm(request.POST, request.FILES, is_agent=agent)
        if form.is_valid():
            comment = TicketComment.objects.create(
                ticket=ticket,
                author=request.user,
                body=form.cleaned_data["body"],
                is_internal=form.cleaned_data.get("is_internal", False) if agent else False,
            )
            for file in request.FILES.getlist("attachments"):
                TicketAttachment.objects.create(comment=comment, file=file, uploaded_by=request.user)

            if not agent and ticket.status in {Ticket.Status.RESUELTO, Ticket.Status.ESPERANDO_CONFIRMACION}:
                ticket.status = Ticket.Status.EN_CURSO
                ticket.save(update_fields=["status", "updated_at"])
                send_status_changed_email(ticket)

            send_comment_email(ticket=ticket, author=request.user, is_internal=comment.is_internal)
            messages.success(request, "Comentario agregado")
            return redirect("tickets:ticket_detail", pk=ticket.pk)
    else:
        form = TicketCommentForm(is_agent=agent)

    update_form = None
    if can_manage_ticket(request.user, ticket):
        update_form = TicketUpdateForm(initial={"status": ticket.status})

    context = {"ticket": ticket, "comments": comments, "form": form, "update_form": update_form, "is_agent": agent}
    return render(request, "tickets/ticket_detail.html", context)


@login_required
def ticket_update(request, pk):
    ticket = _get_ticket_or_404_for_user(request.user, pk)
    if not can_manage_ticket(request.user, ticket):
        raise Http404("No autorizado")

    if request.method != "POST":
        return redirect("tickets:ticket_detail", pk=ticket.pk)

    form = TicketUpdateForm(request.POST, instance=ticket)
    if form.is_valid():
        previous_status = ticket.status
        ticket = form.save(commit=False)

        if form.cleaned_data.get("take_ownership"):
            ticket.assigned_to = request.user
        if form.cleaned_data.get("clear_assignment"):
            ticket.assigned_to = None

        ticket.save()
        if previous_status != ticket.status:
            send_status_changed_email(ticket)
        messages.success(request, "Ticket actualizado")
    else:
        messages.error(request, "No se pudo actualizar el ticket")

    return redirect("tickets:ticket_detail", pk=ticket.pk)
