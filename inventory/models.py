from django.db import models
from django.conf import settings
from products.models import Product


class Stock(models.Model):
    """স্টক ট্র্যাকিং"""
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='stocks'
    )
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock', verbose_name='পণ্য')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='বর্তমান পরিমাণ')
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=10, verbose_name='পুনঃঅর্ডার লেভেল')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'স্টক'
        verbose_name_plural = 'স্টক সমূহ'
    
    def __str__(self):
        return f"{self.product.name}: {self.quantity} {self.product.unit.short_name if self.product.unit else ''}"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level
    
    @property
    def stock_value(self):
        """স্টকের মোট মূল্য (ক্রয় মূল্যে)"""
        return self.quantity * self.product.buying_price
    
    @property
    def stock_selling_value(self):
        """স্টকের মোট মূল্য (বিক্রয় মূল্যে)"""
        return self.quantity * self.product.selling_price


class StockMovement(models.Model):
    """স্টক মুভমেন্ট হিস্ট্রি"""
    MOVEMENT_TYPES = [
        ('in', 'স্টক ইন'),
        ('out', 'স্টক আউট'),
        ('adjustment', 'সমন্বয়'),
        ('return', 'রিটার্ন'),
    ]
    
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='stock_movements'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements', verbose_name='পণ্য')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name='মুভমেন্ট টাইপ')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='পরিমাণ')
    previous_quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='আগের পরিমাণ')
    new_quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='নতুন পরিমাণ')
    reference = models.CharField(max_length=100, blank=True, verbose_name='রেফারেন্স')
    notes = models.TextField(blank=True, verbose_name='নোট')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='তৈরি করেছেন')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'স্টক মুভমেন্ট'
        verbose_name_plural = 'স্টক মুভমেন্ট সমূহ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} ({self.quantity})"


class StockAlert(models.Model):
    """লো স্টক অ্যালার্ট"""
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='stock_alerts'
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='alerts', verbose_name='স্টক')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts', verbose_name='পণ্য')
    message = models.CharField(max_length=255, verbose_name='বার্তা')
    is_read = models.BooleanField(default=False, verbose_name='পড়া হয়েছে')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'স্টক অ্যালার্ট'
        verbose_name_plural = 'স্টক অ্যালার্ট সমূহ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.stock.product.name}: {self.message}"
