from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('', views.accounting_dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_add, name='transaction_add'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    
    # Cash Flow
    path('cashflow/', views.cashflow_list, name='cashflow_list'),
    path('cashflow/today/', views.today_cashflow, name='today_cashflow'),
    
    # Reports
    path('report/profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('report/income/', views.income_report, name='income_report'),
    path('report/expense/', views.expense_report, name='expense_report'),
]
