from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from accounts.permissions import is_agent


@login_required
def home_redirect(request):
    if request.user.is_superuser or is_agent(request.user):
        return redirect("tickets:agent_dashboard")
    return redirect("tickets:user_dashboard")
