from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tenants.urls')),
    path('app/', include('accounts.urls')),
    path('app/products/', include('products.urls')),
    path('app/inventory/', include('inventory.urls')),
    path('app/sales/', include('sales.urls')),
    path('app/purchases/', include('purchases.urls')),
    path('app/accounting/', include('accounting.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Admin site customization
admin.site.site_header = "স্টেশনারি শপ SaaS অ্যাডমিন"
admin.site.site_title = "স্টেশনারি শপ SaaS"
admin.site.index_title = "প্ল্যাটফর্ম ম্যানেজমেন্ট"
