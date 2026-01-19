from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pos/', views.pos, name='pos'),
    path('add/', views.sale_add, name='sale_add'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/invoice/', views.sale_invoice, name='sale_invoice'),
    path('<int:pk>/payment/', views.add_payment, name='add_payment'),
    
    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    
    # Reports
    path('report/daily/', views.daily_sales_report, name='daily_sales_report'),
    path('report/due/', views.due_report, name='due_report'),
    
    # API
    path('api/create/', views.create_sale_api, name='create_sale_api'),
]
