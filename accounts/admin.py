from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'organization', 'role', 'is_owner', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'organization', 'is_owner']
    search_fields = ['username', 'email', 'phone', 'organization__name']
    ordering = ['username']
    autocomplete_fields = ['organization']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('দোকান তথ্য', {'fields': ('organization', 'is_owner')}),
        ('অতিরিক্ত তথ্য', {'fields': ('role', 'phone', 'address', 'profile_image')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('দোকান তথ্য', {'fields': ('organization', 'is_owner')}),
        ('অতিরিক্ত তথ্য', {'fields': ('role', 'phone', 'address')}),
    )
