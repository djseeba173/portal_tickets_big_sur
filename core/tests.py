from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import AgentProfile, Area


User = get_user_model()


class HomeRedirectTests(TestCase):
    def setUp(self):
        self.agent_group, _ = Group.objects.get_or_create(name="Agentes")
        self.user_group, _ = Group.objects.get_or_create(name="Usuarios")
        self.area, _ = Area.objects.get_or_create(name="Infraestructura")

        self.end_user = User.objects.create_user(username="usuario", password="Password123!")
        self.end_user.groups.add(self.user_group)

        self.agent = User.objects.create_user(username="agente", password="Password123!")
        self.agent.groups.add(self.agent_group)
        profile = AgentProfile.objects.create(user=self.agent)
        profile.areas.add(self.area)

        self.admin = User.objects.create_superuser(username="admin", password="Password123!", email="admin@example.com")

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_home_redirects_end_user_to_user_dashboard(self):
        self.client.force_login(self.end_user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("tickets:user_dashboard"))

    def test_home_redirects_agent_to_agent_dashboard(self):
        self.client.force_login(self.agent)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("tickets:agent_dashboard"))

    def test_home_redirects_superuser_to_agent_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("tickets:agent_dashboard"))
