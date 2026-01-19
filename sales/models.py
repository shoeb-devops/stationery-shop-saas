from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.models import Product


class Customer(models.Model):
    """গ্রাহক"""
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='customers'
    )
    name = models.CharField(max_length=200, verbose_name='গ্রাহকের নাম')
    phone = models.CharField(max_length=15, blank=True, verbose_name='ফোন নম্বর')
    email = models.EmailField(blank=True, verbose_name='ইমেইল')
    address = models.TextField(blank=True, verbose_name='ঠিকানা')
    company = models.CharField(max_length=200, blank=True, verbose_name='প্রতিষ্ঠান')
    notes = models.TextField(blank=True, verbose_name='নোট')
    is_active = models.BooleanField(default=True, verbose_name='সক্রিয়')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'গ্রাহক'
        verbose_name_plural = 'গ্রাহকগণ'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_purchases(self):
        """মোট ক্রয়"""
        return self.sales.aggregate(total=models.Sum('grand_total'))['total'] or 0
    
    @property
    def total_due(self):
        """মোট বাকি"""
        return self.sales.aggregate(due=models.Sum('due_amount'))['due'] or 0


class Sale(models.Model):
    """বিক্রয়"""
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
        null=True, blank=True, related_name='sales'
    )
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='ইনভয়েস নম্বর')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales', verbose_name='গ্রাহক')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='উপমোট')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ছাড়')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='ছাড় %')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ট্যাক্স')
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='সর্বমোট')
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='প্রদত্ত টাকা')
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='বাকি টাকা')
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ফেরত')
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid', verbose_name='পেমেন্ট স্ট্যাটাস')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name='পেমেন্ট মাধ্যম')
    
    notes = models.TextField(blank=True, verbose_name='নোট')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='বিক্রেতা')
    sale_date = models.DateTimeField(auto_now_add=True, verbose_name='বিক্রয়ের তারিখ')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'বিক্রয়'
        verbose_name_plural = 'বিক্রয় সমূহ'
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.grand_total}৳"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            today = timezone.now()
            prefix = f"INV-{today.strftime('%Y%m%d')}"
            last_sale = Sale.objects.filter(invoice_number__startswith=prefix).order_by('-id').first()
            if last_sale:
                try:
                    last_num = int(last_sale.invoice_number.split('-')[-1])
                    self.invoice_number = f"{prefix}-{last_num + 1:04d}"
                except:
                    self.invoice_number = f"{prefix}-0001"
            else:
                self.invoice_number = f"{prefix}-0001"
        
        # Calculate totals
        self.due_amount = self.grand_total - self.paid_amount
        if self.due_amount < 0:
            self.change_amount = abs(self.due_amount)
            self.due_amount = 0
        
        # Set payment status
        if self.due_amount == 0 and self.grand_total > 0:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
        
        super().save(*args, **kwargs)
    
    @property
    def profit(self):
        """এই বিক্রয়ে লাভ"""
        total_cost = sum(item.quantity * item.product.buying_price for item in self.items.all())
        return self.grand_total - total_cost


class SaleItem(models.Model):
    """বিক্রয়ের আইটেম"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name='বিক্রয়')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='পণ্য')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name='পরিমাণ')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='একক মূল্য')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ছাড়')
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='মোট')
    
    class Meta:
        verbose_name = 'বিক্রয় আইটেম'
        verbose_name_plural = 'বিক্রয় আইটেম সমূহ'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total = (self.quantity * self.unit_price) - self.discount
        super().save(*args, **kwargs)


class Payment(models.Model):
    """পেমেন্ট রেকর্ড"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments', verbose_name='বিক্রয়')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='টাকার পরিমাণ')
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHODS, verbose_name='পেমেন্ট মাধ্যম')
    reference = models.CharField(max_length=100, blank=True, verbose_name='রেফারেন্স')
    notes = models.TextField(blank=True, verbose_name='নোট')
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='গ্রহণকারী')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='তারিখ')
    
    class Meta:
        verbose_name = 'পেমেন্ট'
        verbose_name_plural = 'পেমেন্ট সমূহ'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.sale.invoice_number} - {self.amount}৳"
