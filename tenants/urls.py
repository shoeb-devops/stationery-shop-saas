from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('register/', views.register, name='register'),
    path('settings/', views.shop_settings, name='settings'),
    path('subscription/', views.subscription_details, name='subscription'),
]
