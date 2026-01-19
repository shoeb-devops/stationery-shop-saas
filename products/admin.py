from django.contrib import admin
from .models import Category, GSMType, PaperSize, Unit, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(GSMType)
class GSMTypeAdmin(admin.ModelAdmin):
    list_display = ['value', 'description']
    ordering = ['value']


@admin.register(PaperSize)
class PaperSizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'width_mm', 'height_mm']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'gsm', 'size', 'buying_price', 'selling_price', 'is_active']
    list_filter = ['category', 'gsm', 'size', 'is_active']
    search_fields = ['name', 'sku', 'barcode']
    readonly_fields = ['sku']
