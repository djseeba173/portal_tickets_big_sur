from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.models import AgentProfile, Area
from tickets.models import Ticket, TicketComment


class Command(BaseCommand):
    help = "Carga datos demo para el portal de tickets"

    def handle(self, *args, **options):
        usuarios_group, _ = Group.objects.get_or_create(name="Usuarios")
        agentes_group, _ = Group.objects.get_or_create(name="Agentes")

        infra, _ = Area.objects.get_or_create(name="Infraestructura", defaults={"description": "Servidores y sistemas"})
        desarrollo, _ = Area.objects.get_or_create(name="Desarrollo", defaults={"description": "Aplicaciones internas"})
        soporte, _ = Area.objects.get_or_create(name="Soporte", defaults={"description": "Asistencia general"})

        superuser, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@local.test", "is_superuser": True, "is_staff": True},
        )
        if created:
            superuser.set_password("Admin1234!")
            superuser.save()

        agente_infra, created = User.objects.get_or_create(
            username="agente_infra",
            defaults={"email": "infra@local.test", "is_staff": True},
        )
        if created:
            agente_infra.set_password("Password123!")
            agente_infra.save()
        agente_infra.groups.add(agentes_group)
        perfil_infra, _ = AgentProfile.objects.get_or_create(user=agente_infra)
        perfil_infra.areas.add(infra, soporte)

        agente_dev, created = User.objects.get_or_create(
            username="agente_dev",
            defaults={"email": "dev@local.test", "is_staff": True},
        )
        if created:
            agente_dev.set_password("Password123!")
            agente_dev.save()
        agente_dev.groups.add(agentes_group)
        perfil_dev, _ = AgentProfile.objects.get_or_create(user=agente_dev)
        perfil_dev.areas.add(desarrollo)

        usuario, created = User.objects.get_or_create(
            username="usuario_demo",
            defaults={"email": "usuario@local.test"},
        )
        if created:
            usuario.set_password("Password123!")
            usuario.save()
        usuario.groups.add(usuarios_group)

        ticket_1, _ = Ticket.objects.get_or_create(
            subject="No puedo acceder a VPN",
            created_by=usuario,
            defaults={"description": "Error de autenticación al conectar", "area": infra, "priority": Ticket.Priority.ALTA},
        )
        ticket_2, _ = Ticket.objects.get_or_create(
            subject="Error en módulo de reportes",
            created_by=usuario,
            defaults={"description": "Falla al exportar en PDF", "area": desarrollo, "priority": Ticket.Priority.MEDIA},
        )

        TicketComment.objects.get_or_create(ticket=ticket_1, author=usuario, body="Ocurre desde hoy temprano")
        TicketComment.objects.get_or_create(ticket=ticket_2, author=agente_dev, body="Estamos revisando el incidente", is_internal=False)

        self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
        self.stdout.write("Usuarios demo: admin / agente_infra / agente_dev / usuario_demo")
