from django import template
from accounts.permissions import has_permission, ROLE_PERMISSIONS

register = template.Library()


@register.simple_tag(takes_context=True)
def user_can_access(context, module):
    """Check if current user can access a module"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return has_permission(request.user, module)


@register.filter
def can_access(user, module):
    """Filter version for template usage: {{ user|can_access:'accounting' }}"""
    if not user.is_authenticated:
        return False
    return has_permission(user, module)


@register.simple_tag(takes_context=True)
def get_user_role_display(context):
    """Get user's role display name"""
    request = context.get('request')
    if request and request.user.is_authenticated:
        return request.user.get_role_display()
    return ''
