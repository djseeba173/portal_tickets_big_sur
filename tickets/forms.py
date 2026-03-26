from django import forms
from django.conf import settings

from .models import Ticket


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultiFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class TicketCreateForm(forms.ModelForm):
    attachments = MultipleFileField(required=False, widget=MultiFileInput(attrs={"class": "form-control"}))

    class Meta:
        model = Ticket
        fields = ["subject", "description", "area", "priority"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "area": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_attachments(self):
        files = self.files.getlist("attachments")
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        for file in files:
            if file.size > max_size:
                raise forms.ValidationError(f"Cada archivo debe ser menor a {settings.MAX_UPLOAD_SIZE_MB} MB")
        return files


class TicketCommentForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}), label="Mensaje")
    is_internal = forms.BooleanField(required=False, label="Nota interna (solo agentes)")
    attachments = MultipleFileField(required=False, widget=MultiFileInput(attrs={"class": "form-control"}))

    def __init__(self, *args, is_agent=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_agent:
            self.fields.pop("is_internal")

    def clean_attachments(self):
        files = self.files.getlist("attachments")
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        for file in files:
            if file.size > max_size:
                raise forms.ValidationError(f"Cada archivo debe ser menor a {settings.MAX_UPLOAD_SIZE_MB} MB")
        return files


class TicketUpdateForm(forms.ModelForm):
    take_ownership = forms.BooleanField(required=False, label="Asignarme este ticket")
    clear_assignment = forms.BooleanField(required=False, label="Quitar asignación")

    class Meta:
        model = Ticket
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }
