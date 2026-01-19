from django.db import models
from django.utils import timezone
from decimal import Decimal


class SubscriptionPlan(models.Model):
    """সাবস্ক্রিপশন প্ল্যান"""
    PLAN_CHOICES = [
        ('free', 'ফ্রি'),
        ('basic', 'বেসিক'),
        ('premium', 'প্রিমিয়াম'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Limits
    max_products = models.IntegerField(default=50, help_text="সর্বোচ্চ পণ্য সংখ্যা")
    max_users = models.IntegerField(default=1, help_text="সর্বোচ্চ ইউজার সংখ্যা")
    max_monthly_sales = models.IntegerField(default=100, help_text="মাসিক সর্বোচ্চ বিক্রি")
    
    # Features
    has_reports = models.BooleanField(default=True)
    has_barcode = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_multiple_locations = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "সাবস্ক্রিপশন প্ল্যান"
        verbose_name_plural = "সাবস্ক্রিপশন প্ল্যান"
    
    def __str__(self):
        return self.display_name


class Organization(models.Model):
    """দোকান/প্রতিষ্ঠান (Tenant)"""
    name = models.CharField(max_length=200, verbose_name="দোকানের নাম")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL friendly name")
    
    # Contact Info
    owner_name = models.CharField(max_length=200, verbose_name="মালিকের নাম")
    email = models.EmailField(verbose_name="ইমেইল")
    phone = models.CharField(max_length=20, verbose_name="ফোন")
    address = models.TextField(blank=True, verbose_name="ঠিকানা")
    
    # Branding
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)
    
    # Subscription
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "দোকান"
        verbose_name_plural = "দোকান সমূহ"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def active_subscription(self):
        return self.subscriptions.filter(is_active=True, end_date__gte=timezone.now()).first()
    
    def get_current_product_count(self):
        return self.products.count()
    
    def get_current_user_count(self):
        return self.users.count()
    
    def can_add_product(self):
        if not self.plan:
            return False
        return self.get_current_product_count() < self.plan.max_products
    
    def can_add_user(self):
        if not self.plan:
            return False
        return self.get_current_user_count() < self.plan.max_users


class Subscription(models.Model):
    """সাবস্ক্রিপশন রেকর্ড"""
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'মাসিক'),
        ('yearly', 'বার্ষিক'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'সক্রিয়'),
        ('expired', 'মেয়াদ শেষ'),
        ('cancelled', 'বাতিল'),
        ('pending', 'পেন্ডিং'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=False)
    
    # Payment info
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "সাবস্ক্রিপশন"
        verbose_name_plural = "সাবস্ক্রিপশন"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.plan.display_name}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.end_date
    
    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now()).days


class TenantAwareManager(models.Manager):
    """Tenant-aware queryset manager"""
    
    def for_organization(self, organization):
        return self.get_queryset().filter(organization=organization)
