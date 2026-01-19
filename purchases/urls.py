from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.purchase_list, name='purchase_list'),
    path('add/', views.purchase_add, name='purchase_add'),
    path('<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('<int:pk>/payment/', views.add_payment, name='add_payment'),
    
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    
    # Reports
    path('report/', views.purchase_report, name='purchase_report'),
    path('report/due/', views.supplier_due_report, name='supplier_due_report'),
]
