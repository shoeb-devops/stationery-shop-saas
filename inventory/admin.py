from django.contrib import admin
from .models import Stock, StockMovement, StockAlert


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'reorder_level', 'is_low_stock', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['product__name']
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'লো স্টক'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference']
    readonly_fields = ['previous_quantity', 'new_quantity']


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['stock', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
