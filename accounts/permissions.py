"""
Permission decorators for role-based access control
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


# Define which roles can access which modules
ROLE_PERMISSIONS = {
    'admin': ['all'],  # Admin can access everything
    'manager': ['accounting', 'accounting_dashboard', 'transactions', 'expenses', 'reports', 'profit_loss'],
    'accountant': ['accounting', 'accounting_dashboard', 'transactions', 'expenses', 'reports', 'profit_loss', 'sales_reports', 'purchase_reports'],
    'staff': ['pos', 'sales', 'products_view'],
}


def has_permission(user, module):
    """Check if user has permission to access a module"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if user.role == 'admin':
        return True
    
    allowed_modules = ROLE_PERMISSIONS.get(user.role, [])
    
    if 'all' in allowed_modules:
        return True
    
    return module in allowed_modules


def permission_required(module):
    """Decorator to check module permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, module):
                messages.error(request, 'আপনার এই সেকশনে অ্যাক্সেস নেই!')
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Only admin/superuser can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or request.user.role == 'admin'):
            messages.error(request, 'শুধুমাত্র অ্যাডমিন এই পেজ দেখতে পারবেন!')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Manager or above can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or request.user.role in ['admin', 'manager']):
            messages.error(request, 'আপনার এই সেকশনে অ্যাক্সেস নেই!')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def accountant_required(view_func):
    """Accountant or above can access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or request.user.role in ['admin', 'manager', 'accountant']):
            messages.error(request, 'আপনার এই সেকশনে অ্যাক্সেস নেই!')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
