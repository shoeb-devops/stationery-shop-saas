from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """কাস্টম ইউজার মডেল"""
    
    ROLE_CHOICES = [
        ('admin', 'অ্যাডমিন'),
        ('manager', 'ম্যানেজার'),
        ('staff', 'স্টাফ'),
        ('accountant', 'হিসাবরক্ষক'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff', verbose_name='ভূমিকা')
    phone = models.CharField(max_length=15, blank=True, verbose_name='ফোন নম্বর')
    address = models.TextField(blank=True, verbose_name='ঠিকানা')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='প্রোফাইল ছবি')
    
    # SaaS fields
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='দোকান'
    )
    is_owner = models.BooleanField(default=False, verbose_name='মালিক')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'ব্যবহারকারী'
        verbose_name_plural = 'ব্যবহারকারীগণ'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    def is_manager(self):
        return self.role in ['admin', 'manager'] or self.is_superuser
    
    def is_accountant(self):
        return self.role in ['admin', 'accountant'] or self.is_superuser
    
    def is_saas_admin(self):
        """Check if user is SaaS platform admin (no organization)"""
        return self.is_superuser and not self.organization
