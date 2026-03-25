from django.contrib import admin

from .models import AgentProfile, Area


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    filter_horizontal = ("areas",)
    search_fields = ("user__username", "user__email")
