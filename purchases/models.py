from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.models import Product


class Supplier(models.Model):
    """সাপ্লায়ার"""
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='suppliers'
    )
    name = models.CharField(max_length=200, verbose_name='সাপ্লায়ারের নাম')
    company = models.CharField(max_length=200, blank=True, verbose_name='কোম্পানি')
    phone = models.CharField(max_length=15, blank=True, verbose_name='ফোন নম্বর')
    email = models.EmailField(blank=True, verbose_name='ইমেইল')
    address = models.TextField(blank=True, verbose_name='ঠিকানা')
    notes = models.TextField(blank=True, verbose_name='নোট')
    is_active = models.BooleanField(default=True, verbose_name='সক্রিয়')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'সাপ্লায়ার'
        verbose_name_plural = 'সাপ্লায়ারগণ'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name
    
    @property
    def total_purchases(self):
        """মোট ক্রয়"""
        return self.purchases.aggregate(total=models.Sum('grand_total'))['total'] or 0
    
    @property
    def total_due(self):
        """মোট বাকি"""
        return self.purchases.aggregate(due=models.Sum('due_amount'))['due'] or 0


class Purchase(models.Model):
    """ক্রয়"""
    PAYMENT_STATUS = [
        ('paid', 'পরিশোধিত'),
        ('partial', 'আংশিক'),
        ('unpaid', 'অপরিশোধিত'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'নগদ'),
        ('card', 'কার্ড'),
        ('mobile', 'মোবাইল ব্যাংকিং'),
        ('bank', 'ব্যাংক ট্রান্সফার'),
        ('credit', 'বাকি'),
    ]
    
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='purchases'
    )
    purchase_number = models.CharField(max_length=50, unique=True, verbose_name='ক্রয় নম্বর')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='purchases', verbose_name='সাপ্লায়ার')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='উপমোট')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ছাড়')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ট্যাক্স')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='শিপিং খরচ')
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='সর্বমোট')
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='প্রদত্ত টাকা')
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='বাকি টাকা')
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid', verbose_name='পেমেন্ট স্ট্যাটাস')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name='পেমেন্ট মাধ্যম')
    
    notes = models.TextField(blank=True, verbose_name='নোট')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='তৈরি করেছেন')
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name='ক্রয়ের তারিখ')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'ক্রয়'
        verbose_name_plural = 'ক্রয় সমূহ'
        ordering = ['-purchase_date']
    
    def __str__(self):
        return f"{self.purchase_number} - {self.grand_total}৳"
    
    def save(self, *args, **kwargs):
        if not self.purchase_number:
            from django.utils import timezone
            today = timezone.now()
            prefix = f"PUR-{today.strftime('%Y%m%d')}"
            last_purchase = Purchase.objects.filter(purchase_number__startswith=prefix).order_by('-id').first()
            if last_purchase:
                try:
                    last_num = int(last_purchase.purchase_number.split('-')[-1])
                    self.purchase_number = f"{prefix}-{last_num + 1:04d}"
                except:
                    self.purchase_number = f"{prefix}-0001"
            else:
                self.purchase_number = f"{prefix}-0001"
        
        # Calculate totals
        self.due_amount = self.grand_total - self.paid_amount
        
        # Set payment status
        if self.due_amount <= 0 and self.grand_total > 0:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
        
        super().save(*args, **kwargs)


class PurchaseItem(models.Model):
    """ক্রয়ের আইটেম"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items', verbose_name='ক্রয়')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='পণ্য')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name='পরিমাণ')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='একক মূল্য')
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='মোট')
    
    class Meta:
        verbose_name = 'ক্রয় আইটেম'
        verbose_name_plural = 'ক্রয় আইটেম সমূহ'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SupplierPayment(models.Model):
    """সাপ্লায়ার পেমেন্ট"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='payments', verbose_name='ক্রয়')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='টাকার পরিমাণ')
    payment_method = models.CharField(max_length=20, choices=Purchase.PAYMENT_METHODS, verbose_name='পেমেন্ট মাধ্যম')
    reference = models.CharField(max_length=100, blank=True, verbose_name='রেফারেন্স')
    notes = models.TextField(blank=True, verbose_name='নোট')
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='প্রদানকারী')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='তারিখ')
    
    class Meta:
        verbose_name = 'সাপ্লায়ার পেমেন্ট'
        verbose_name_plural = 'সাপ্লায়ার পেমেন্ট সমূহ'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.purchase.purchase_number} - {self.amount}৳"
