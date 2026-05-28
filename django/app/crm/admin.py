from django.contrib import admin
from .models import Customer, FollowUp


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'institution',
        'lab_group',
        'phone',
        'status',
        'source',
        'assigned_to',
        'created_at',
    )

    search_fields = (
        'name',
        'institution',
        'lab_group',
        'phone',
        'email',
        'research_direction',
    )

    list_filter = (
        'status',
        'source',
        'created_at',
    )

    ordering = ('-created_at',)

    autocomplete_fields = (
        'assigned_to',
    )

    date_hierarchy = 'created_at'


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'customer',
        'follow_type',
        'next_date',
        'created_by',
        'created_at',
    )

    search_fields = (
        'customer__name',
        'content',
        'next_action',
    )

    list_filter = (
        'follow_type',
        'created_at',
        'next_date',
    )

    autocomplete_fields = (
        'customer',
        'created_by',
    )

    ordering = ('-created_at',)

    date_hierarchy = 'created_at'
