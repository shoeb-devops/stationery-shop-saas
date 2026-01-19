from django.db import models
from django.conf import settings
from django.utils import timezone


class Transaction(models.Model):
    """লেনদেন রেকর্ড"""
    TRANSACTION_TYPES = [
        ('income', 'আয়'),
        ('expense', 'ব্যয়'),
    ]
    
    CATEGORIES = [
        ('sale', 'বিক্রয়'),
        ('purchase', 'ক্রয়'),
        ('payment_received', 'পেমেন্ট গ্রহণ'),
        ('payment_made', 'পেমেন্ট প্রদান'),
        ('salary', 'বেতন'),
        ('rent', 'ভাড়া'),
        ('utility', 'ইউটিলিটি বিল'),
        ('transport', 'পরিবহন'),
        ('other', 'অন্যান্য'),
    ]
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name='লেনদেনের ধরণ')
    category = models.CharField(max_length=30, choices=CATEGORIES, verbose_name='ক্যাটাগরি')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='টাকার পরিমাণ')
    description = models.TextField(verbose_name='বিবরণ')
    reference = models.CharField(max_length=100, blank=True, verbose_name='রেফারেন্স')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='তৈরি করেছেন')
    transaction_date = models.DateField(default=timezone.now, verbose_name='তারিখ')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'লেনদেন'
        verbose_name_plural = 'লেনদেন সমূহ'
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}৳ ({self.get_category_display()})"


class DailyCashFlow(models.Model):
    """দৈনিক ক্যাশ ফ্লো"""
    date = models.DateField(unique=True, verbose_name='তারিখ')
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='প্রারম্ভিক ব্যালেন্স')
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='মোট আয়')
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='মোট ব্যয়')
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='সমাপনী ব্যালেন্স')
    notes = models.TextField(blank=True, verbose_name='নোট')
    is_closed = models.BooleanField(default=False, verbose_name='বন্ধ')
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='বন্ধ করেছেন')
    
    class Meta:
        verbose_name = 'দৈনিক ক্যাশ ফ্লো'
        verbose_name_plural = 'দৈনিক ক্যাশ ফ্লো সমূহ'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - Opening: {self.opening_balance}৳, Closing: {self.closing_balance}৳"
    
    def calculate_closing(self):
        self.closing_balance = self.opening_balance + self.total_income - self.total_expense
        return self.closing_balance


class Expense(models.Model):
    """খরচ রেকর্ড"""
    EXPENSE_CATEGORIES = [
        ('rent', 'দোকান ভাড়া'),
        ('salary', 'বেতন'),
        ('electricity', 'বিদ্যুৎ বিল'),
        ('water', 'পানি বিল'),
        ('internet', 'ইন্টারনেট বিল'),
        ('transport', 'পরিবহন'),
        ('packaging', 'প্যাকেজিং'),
        ('maintenance', 'মেরামত'),
        ('marketing', 'মার্কেটিং'),
        ('other', 'অন্যান্য'),
    ]
    
    category = models.CharField(max_length=30, choices=EXPENSE_CATEGORIES, verbose_name='ক্যাটাগরি')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='টাকার পরিমাণ')
    description = models.TextField(blank=True, verbose_name='বিবরণ')
    expense_date = models.DateField(default=timezone.now, verbose_name='তারিখ')
    receipt = models.ImageField(upload_to='expenses/', blank=True, null=True, verbose_name='রিসিট')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='তৈরি করেছেন')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'খরচ'
        verbose_name_plural = 'খরচ সমূহ'
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}৳"
