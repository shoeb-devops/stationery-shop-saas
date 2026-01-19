from django.contrib import admin
from .models import Organization, SubscriptionPlan, Subscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'price_monthly', 'max_products', 'max_users', 'is_active']
    list_filter = ['is_active']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner_name', 'email', 'phone', 'plan', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'plan']
    search_fields = ['name', 'owner_name', 'email', 'phone']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'status', 'start_date', 'end_date', 'is_active']
    list_filter = ['status', 'is_active', 'plan']
    search_fields = ['organization__name']
    date_hierarchy = 'created_at'
