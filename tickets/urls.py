from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("mis-tickets/", views.user_dashboard, name="user_dashboard"),
    path("panel-agente/", views.agent_dashboard, name="agent_dashboard"),
    path("nuevo/", views.ticket_create, name="ticket_create"),
    path("<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("<int:pk>/actualizar/", views.ticket_update, name="ticket_update"),
]
