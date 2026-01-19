from django.contrib import admin
from .models import Customer, Sale, SaleItem, Payment


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ['total']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'company', 'total_due', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'phone', 'company']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'grand_total', 'paid_amount', 'due_amount', 'payment_status', 'sale_date']
    list_filter = ['payment_status', 'payment_method', 'sale_date']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['invoice_number', 'subtotal', 'grand_total', 'due_amount', 'change_amount']
    inlines = [SaleItemInline, PaymentInline]
    date_hierarchy = 'sale_date'


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'total']
    search_fields = ['sale__invoice_number', 'product__name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['sale', 'amount', 'payment_method', 'received_by', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['sale__invoice_number']
