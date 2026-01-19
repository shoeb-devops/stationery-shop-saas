from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """কাগজের ক্যাটাগরি"""
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE, 
        null=True, blank=True, related_name='categories'
    )
    name = models.CharField(max_length=100, verbose_name='ক্যাটাগরির নাম')
    description = models.TextField(blank=True, verbose_name='বিবরণ')
    is_active = models.BooleanField(default=True, verbose_name='সক্রিয়')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'ক্যাটাগরি'
        verbose_name_plural = 'ক্যাটাগরিসমূহ'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GSMType(models.Model):
    """GSM (কাগজের পুরুত্ব) টাইপ - Global, not per org"""
    value = models.PositiveIntegerField(unique=True, verbose_name='GSM মান')
    description = models.CharField(max_length=100, blank=True, verbose_name='বিবরণ')
    
    class Meta:
        verbose_name = 'GSM টাইপ'
        verbose_name_plural = 'GSM টাইপসমূহ'
        ordering = ['value']
    
    def __str__(self):
        return f"{self.value} GSM"


class PaperSize(models.Model):
    """কাগজের সাইজ - Global, not per org"""
    name = models.CharField(max_length=50, unique=True, verbose_name='সাইজের নাম')
    width_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='প্রস্থ (মিমি)')
    height_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='দৈর্ঘ্য (মিমি)')
    
    class Meta:
        verbose_name = 'কাগজের সাইজ'
        verbose_name_plural = 'কাগজের সাইজসমূহ'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Unit(models.Model):
    """পরিমাপের একক - Global, not per org"""
    name = models.CharField(max_length=50, unique=True, verbose_name='একক')
    short_name = models.CharField(max_length=10, verbose_name='সংক্ষিপ্ত নাম')
    
    class Meta:
        verbose_name = 'একক'
        verbose_name_plural = 'একক সমূহ'
    
    def __str__(self):
        return f"{self.name} ({self.short_name})"


class Product(models.Model):
    """প্রোডাক্ট / কাগজ"""
    organization = models.ForeignKey(
        'tenants.Organization', on_delete=models.CASCADE,
        null=True, blank=True, related_name='products'
    )
    name = models.CharField(max_length=200, verbose_name='পণ্যের নাম')
    sku = models.CharField(max_length=50, unique=True, blank=True, verbose_name='SKU কোড')
    barcode = models.CharField(max_length=50, blank=True, verbose_name='বারকোড')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='ক্যাটাগরি')
    gsm = models.ForeignKey(GSMType, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='GSM')
    size = models.ForeignKey(PaperSize, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='সাইজ')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='একক')
    
    buying_price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='ক্রয় মূল্য (৳)'
    )
    selling_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='বিক্রয় মূল্য (৳)'
    )
    
    description = models.TextField(blank=True, verbose_name='বিবরণ')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='ছবি')
    is_active = models.BooleanField(default=True, verbose_name='সক্রিয়')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'পণ্য'
        verbose_name_plural = 'পণ্যসমূহ'
        ordering = ['name']
    
    def __str__(self):
        parts = [self.name]
        if self.gsm:
            parts.append(f"({self.gsm.value} GSM)")
        if self.size:
            parts.append(f"- {self.size.name}")
        return " ".join(parts)
    
    def save(self, *args, **kwargs):
        if not self.sku:
            # Auto generate SKU
            prefix = self.category.name[:3].upper() if self.category else 'PRD'
            last_product = Product.objects.filter(sku__startswith=prefix).order_by('-id').first()
            if last_product and last_product.sku:
                try:
                    last_num = int(last_product.sku.split('-')[-1])
                    self.sku = f"{prefix}-{last_num + 1:04d}"
                except:
                    self.sku = f"{prefix}-0001"
            else:
                self.sku = f"{prefix}-0001"
        super().save(*args, **kwargs)
    
    @property
    def profit_margin(self):
        """লাভের পরিমাণ"""
        return self.selling_price - self.buying_price
    
    @property
    def profit_percentage(self):
        """লাভের শতাংশ"""
        if self.buying_price > 0:
            return ((self.selling_price - self.buying_price) / self.buying_price) * 100
        return 0
