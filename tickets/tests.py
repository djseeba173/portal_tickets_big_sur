import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from accounts.models import AgentProfile, Area
from tickets.forms import TicketCreateForm
from tickets.models import Ticket, TicketAttachment, TicketComment


User = get_user_model()
TEST_MEDIA_ROOT = str(Path(__file__).resolve().parent.parent / ".test_media")


def tearDownModule():
    shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


@override_settings(
    MEDIA_ROOT=TEST_MEDIA_ROOT,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class TicketFlowTests(TestCase):
    def setUp(self):
        self.agent_group, _ = Group.objects.get_or_create(name="Agentes")
        self.user_group, _ = Group.objects.get_or_create(name="Usuarios")

        self.area_infra, _ = Area.objects.get_or_create(name="Infraestructura")
        self.area_dev, _ = Area.objects.get_or_create(name="Desarrollo")

        self.end_user = User.objects.create_user(
            username="usuario_demo",
            password="Password123!",
            email="usuario@example.com",
        )
        self.end_user.groups.add(self.user_group)

        self.other_user = User.objects.create_user(
            username="otro_usuario",
            password="Password123!",
            email="otro@example.com",
        )
        self.other_user.groups.add(self.user_group)

        self.agent = User.objects.create_user(
            username="agente_infra",
            password="Password123!",
            email="agente@example.com",
        )
        self.agent.groups.add(self.agent_group)
        profile = AgentProfile.objects.create(user=self.agent)
        profile.areas.add(self.area_infra)

        self.other_agent = User.objects.create_user(
            username="agente_dev",
            password="Password123!",
            email="agente-dev@example.com",
        )
        self.other_agent.groups.add(self.agent_group)
        other_profile = AgentProfile.objects.create(user=self.other_agent)
        other_profile.areas.add(self.area_dev)

        self.admin = User.objects.create_superuser(
            username="admin",
            password="Password123!",
            email="admin@example.com",
        )

        self.ticket = Ticket.objects.create(
            subject="VPN caída",
            description="No conecta desde la oficina",
            area=self.area_infra,
            priority=Ticket.Priority.ALTA,
            created_by=self.end_user,
        )

    def test_user_dashboard_only_lists_user_tickets(self):
        foreign_ticket = Ticket.objects.create(
            subject="Error ajeno",
            description="No debería verse",
            area=self.area_infra,
            created_by=self.other_user,
        )
        self.client.force_login(self.end_user)

        response = self.client.get(reverse("tickets:user_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket.subject)
        self.assertNotContains(response, foreign_ticket.subject)

    def test_agent_dashboard_only_lists_tickets_from_assigned_areas(self):
        dev_ticket = Ticket.objects.create(
            subject="Bug en exportación",
            description="Error PDF",
            area=self.area_dev,
            created_by=self.end_user,
        )
        self.client.force_login(self.agent)

        response = self.client.get(reverse("tickets:agent_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket.subject)
        self.assertNotContains(response, dev_ticket.subject)

    def test_end_user_is_redirected_away_from_agent_dashboard(self):
        self.client.force_login(self.end_user)

        response = self.client.get(reverse("tickets:agent_dashboard"))

        self.assertRedirects(response, reverse("tickets:user_dashboard"))

    @patch("tickets.views.send_ticket_created_emails")
    def test_user_can_create_ticket_with_multiple_attachments(self, mocked_email):
        self.client.force_login(self.end_user)
        first_file = SimpleUploadedFile("evidencia 1.txt", b"uno", content_type="text/plain")
        second_file = SimpleUploadedFile("evidencia 2.txt", b"dos", content_type="text/plain")

        response = self.client.post(
            reverse("tickets:ticket_create"),
            {
                "subject": "Nuevo incidente",
                "description": "Hay un problema",
                "area": self.area_infra.pk,
                "priority": Ticket.Priority.MEDIA,
                "attachments": [first_file, second_file],
            },
        )

        created_ticket = Ticket.objects.get(subject="Nuevo incidente")
        attachments = list(created_ticket.attachments.all())

        self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": created_ticket.pk}))
        self.assertEqual(created_ticket.created_by, self.end_user)
        self.assertEqual(len(attachments), 2)
        self.assertEqual({attachment.uploaded_by_id for attachment in attachments}, {self.end_user.id})
        mocked_email.assert_called_once_with(created_ticket)

    def test_ticket_create_form_accepts_multiple_files(self):
        files = MultiValueDict(
            {
                "attachments": [
                    SimpleUploadedFile("uno.txt", b"uno", content_type="text/plain"),
                    SimpleUploadedFile("dos.txt", b"dos", content_type="text/plain"),
                ]
            }
        )
        form = TicketCreateForm(
            data={
                "subject": "Incidente",
                "description": "Detalle",
                "area": str(self.area_infra.pk),
                "priority": Ticket.Priority.MEDIA,
            },
            files=files,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data["attachments"]), 2)

    def test_creator_can_view_own_ticket_but_not_foreign_ticket(self):
        self.client.force_login(self.end_user)

        own_response = self.client.get(reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertEqual(own_response.status_code, 200)

        foreign_ticket = Ticket.objects.create(
            subject="Privado",
            description="No visible",
            area=self.area_infra,
            created_by=self.other_user,
        )
        foreign_response = self.client.get(reverse("tickets:ticket_detail", kwargs={"pk": foreign_ticket.pk}))

        self.assertEqual(foreign_response.status_code, 404)

    def test_agent_can_view_ticket_from_owned_area_but_not_other_area(self):
        self.client.force_login(self.agent)

        own_area_response = self.client.get(reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertEqual(own_area_response.status_code, 200)

        dev_ticket = Ticket.objects.create(
            subject="Solo desarrollo",
            description="No visible para infra",
            area=self.area_dev,
            created_by=self.end_user,
        )
        foreign_area_response = self.client.get(reverse("tickets:ticket_detail", kwargs={"pk": dev_ticket.pk}))

        self.assertEqual(foreign_area_response.status_code, 404)

    @patch("tickets.views.send_comment_email")
    def test_agent_can_add_internal_comment_and_user_cannot_see_it(self, mocked_email):
        self.client.force_login(self.agent)

        response = self.client.post(
            reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}),
            {
                "add_comment": "1",
                "body": "Revisando logs del servidor",
                "is_internal": "on",
            },
        )

        comment = TicketComment.objects.get(ticket=self.ticket)
        self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertTrue(comment.is_internal)
        mocked_email.assert_called_once_with(ticket=self.ticket, author=self.agent, is_internal=True)

        self.client.force_login(self.end_user)
        detail_response = self.client.get(reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))

        self.assertNotContains(detail_response, "Revisando logs del servidor")

    @patch("tickets.views.send_comment_email")
    @patch("tickets.views.send_status_changed_email")
    def test_end_user_comment_reopens_resolved_ticket(self, mocked_status_email, mocked_comment_email):
        self.ticket.status = Ticket.Status.RESUELTO
        self.ticket.save(update_fields=["status"])
        self.client.force_login(self.end_user)

        response = self.client.post(
            reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}),
            {
                "add_comment": "1",
                "body": "Sigue fallando",
            },
        )

        self.ticket.refresh_from_db()
        self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertEqual(self.ticket.status, Ticket.Status.EN_CURSO)
        mocked_status_email.assert_called_once_with(self.ticket)
        mocked_comment_email.assert_called_once_with(ticket=self.ticket, author=self.end_user, is_internal=False)

    def test_closed_ticket_rejects_new_comments(self):
        self.ticket.status = Ticket.Status.CERRADO
        self.ticket.save(update_fields=["status"])
        self.client.force_login(self.end_user)

        response = self.client.post(
            reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}),
            {
                "add_comment": "1",
                "body": "No debería guardarse",
            },
        )

        self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertFalse(TicketComment.objects.filter(ticket=self.ticket).exists())

    @patch("tickets.views.send_status_changed_email")
    def test_agent_can_update_status_and_take_ownership(self, mocked_status_email):
        self.client.force_login(self.agent)

        response = self.client.post(
            reverse("tickets:ticket_update", kwargs={"pk": self.ticket.pk}),
            {
                "status": Ticket.Status.EN_CURSO,
                "take_ownership": "on",
            },
        )

        self.ticket.refresh_from_db()
        self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertEqual(self.ticket.status, Ticket.Status.EN_CURSO)
        self.assertEqual(self.ticket.assigned_to, self.agent)
        mocked_status_email.assert_called_once_with(self.ticket)

    def test_end_user_cannot_update_ticket(self):
        self.client.force_login(self.end_user)

        response = self.client.post(
            reverse("tickets:ticket_update", kwargs={"pk": self.ticket.pk}),
            {"status": Ticket.Status.CERRADO},
        )

        self.assertEqual(response.status_code, 404)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.PENDIENTE)

    def test_comment_can_store_multiple_attachments(self):
        self.client.force_login(self.agent)
        first_file = SimpleUploadedFile("respuesta 1.txt", b"uno", content_type="text/plain")
        second_file = SimpleUploadedFile("respuesta 2.txt", b"dos", content_type="text/plain")

        response = self.client.post(
            reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}),
            {
                "add_comment": "1",
                "body": "Adjunto evidencia",
                "attachments": [first_file, second_file],
            },
        )

        comment = TicketComment.objects.get(ticket=self.ticket)
        attachments = list(comment.attachments.all())

        self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": self.ticket.pk}))
        self.assertEqual(len(attachments), 2)
        self.assertEqual({attachment.uploaded_by_id for attachment in attachments}, {self.agent.id})


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TicketAttachmentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="usuario", password="Password123!")
        self.area = Area.objects.create(name="Soporte")
        self.ticket = Ticket.objects.create(
            subject="Incidente",
            description="Detalle",
            area=self.area,
            created_by=self.user,
        )

    def test_attachment_must_belong_to_ticket_or_comment_but_not_both(self):
        comment = TicketComment.objects.create(ticket=self.ticket, author=self.user, body="Comentario")
        attachment = TicketAttachment(
            ticket=self.ticket,
            comment=comment,
            uploaded_by=self.user,
            file=SimpleUploadedFile("archivo.txt", b"contenido", content_type="text/plain"),
        )

        with self.assertRaisesMessage(ValidationError, "El adjunto debe pertenecer al ticket o al comentario, no a ambos."):
            attachment.save()
