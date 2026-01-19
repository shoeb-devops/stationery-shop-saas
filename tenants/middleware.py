from threading import local

_thread_locals = local()


def get_current_organization():
    """Get current organization from thread local"""
    return getattr(_thread_locals, 'organization', None)


def set_current_organization(organization):
    """Set current organization in thread local"""
    _thread_locals.organization = organization


class TenantMiddleware:
    """
    Middleware to detect and set current tenant/organization
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Clear any previous organization
        set_current_organization(None)
        
        # Set organization from logged in user
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'organization') and request.user.organization:
                organization = request.user.organization
                set_current_organization(organization)
                request.organization = organization
            else:
                request.organization = None
        else:
            request.organization = None
        
        response = self.get_response(request)
        return response
