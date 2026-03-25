from accounts.permissions import is_agent


def can_view_ticket(user, ticket) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if is_agent(user):
        profile = getattr(user, "agent_profile", None)
        return bool(profile and profile.areas.filter(pk=ticket.area_id).exists())
    return ticket.created_by_id == user.id


def can_manage_ticket(user, ticket) -> bool:
    if user.is_superuser:
        return True
    return is_agent(user) and can_view_ticket(user, ticket)
