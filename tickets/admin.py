from django.contrib import admin

from .models import Ticket, TicketAttachment, TicketComment


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "area", "status", "priority", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "priority", "area")
    search_fields = ("subject", "description", "created_by__username")
    inlines = [TicketCommentInline, TicketAttachmentInline]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "author", "is_internal", "created_at")
    list_filter = ("is_internal",)
    search_fields = ("ticket__subject", "author__username", "body")


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "comment", "uploaded_by", "uploaded_at")
    search_fields = ("uploaded_by__username",)
