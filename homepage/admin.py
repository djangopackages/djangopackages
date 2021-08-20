from django.contrib import admin

from homepage.models import Dpotw, Gotw, PSA


@admin.register(Dpotw)
class DpotwAdmin(admin.ModelAdmin):
    list_display = ["package", "start_date", "end_date"]
    ordering = ["-start_date", "-end_date"]
    raw_id_fields = ["package"]


@admin.register(Gotw)
class GotwAdmin(admin.ModelAdmin):
    ordering = ["-start_date", "-end_date"]
    list_display = ["grid", "start_date", "end_date"]
    raw_id_fields = ["grid"]


@admin.register(PSA)
class PSAAdmin(admin.ModelAdmin):
    pass
