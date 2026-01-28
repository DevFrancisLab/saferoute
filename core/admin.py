from django.contrib import admin
from .models import Hazard, Report, AlertLog


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    list_display = ('type', 'severity', 'latitude', 'longitude', 'expires_at', 'created_at')
    list_filter = ('type', 'severity', 'created_at')
    search_fields = ('latitude', 'longitude')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Hazard Information', {
            'fields': ('type', 'severity')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        }),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'hazard_type', 'latitude', 'longitude', 'created_at')
    list_filter = ('hazard_type', 'created_at')
    search_fields = ('phone_number', 'latitude', 'longitude')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Contact', {
            'fields': ('phone_number',)
        }),
        ('Hazard Details', {
            'fields': ('hazard_type',)
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'hazard', 'channel', 'sent_at')
    list_filter = ('channel', 'sent_at')
    search_fields = ('phone_number',)
    readonly_fields = ('sent_at',)
    fieldsets = (
        ('Alert Details', {
            'fields': ('phone_number', 'channel', 'hazard')
        }),
        ('Timestamps', {
            'fields': ('sent_at',)
        }),
    )
