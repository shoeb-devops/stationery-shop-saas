from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('low-stock/', views.low_stock, name='low_stock'),
    path('movements/', views.movement_list, name='movement_list'),
    path('adjust/<int:pk>/', views.stock_adjust, name='stock_adjust'),
    path('alerts/', views.alerts, name='alerts'),
    path('report/', views.inventory_report, name='inventory_report'),
]
