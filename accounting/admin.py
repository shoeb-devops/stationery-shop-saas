from django.contrib import admin
from .models import Transaction, DailyCashFlow, Expense


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'category', 'amount', 'description', 'transaction_date']
    list_filter = ['transaction_type', 'category', 'transaction_date']
    search_fields = ['description', 'reference']
    date_hierarchy = 'transaction_date'


@admin.register(DailyCashFlow)
class DailyCashFlowAdmin(admin.ModelAdmin):
    list_display = ['date', 'opening_balance', 'total_income', 'total_expense', 'closing_balance', 'is_closed']
    list_filter = ['is_closed']
    date_hierarchy = 'date'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'expense_date', 'created_by']
    list_filter = ['category', 'expense_date']
    search_fields = ['description']
    date_hierarchy = 'expense_date'
