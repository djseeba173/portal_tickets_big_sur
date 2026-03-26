from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountsRouteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="usuario", password="Password123!")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingresar")

    def test_accounts_base_redirects_anonymous_user_to_login(self):
        response = self.client.get("/accounts/")

        self.assertRedirects(response, f"{reverse('login')}?next=/accounts/")

    def test_accounts_base_redirects_authenticated_user_to_home(self):
        self.client.force_login(self.user)

        response = self.client.get("/accounts/")

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_via_post_clears_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
