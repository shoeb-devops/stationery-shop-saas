from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_add, name='product_add'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    
    # GSM Types
    path('gsm/', views.gsm_list, name='gsm_list'),
    
    # API endpoints
    path('api/search/', views.product_search, name='product_search'),
    path('api/<int:pk>/', views.product_api, name='product_api'),
]
