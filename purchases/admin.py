from django.contrib import admin
from .models import Supplier, Purchase, PurchaseItem, SupplierPayment


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    readonly_fields = ['total']


class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'phone', 'total_due', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'company', 'phone']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_number', 'supplier', 'grand_total', 'paid_amount', 'due_amount', 'payment_status', 'purchase_date']
    list_filter = ['payment_status', 'payment_method', 'purchase_date']
    search_fields = ['purchase_number', 'supplier__name']
    readonly_fields = ['purchase_number', 'subtotal', 'grand_total', 'due_amount']
    inlines = [PurchaseItemInline, SupplierPaymentInline]
    date_hierarchy = 'purchase_date'


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'product', 'quantity', 'unit_price', 'total']
    search_fields = ['purchase__purchase_number', 'product__name']


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'amount', 'payment_method', 'paid_by', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
