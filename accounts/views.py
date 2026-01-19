from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import User
from sales.models import Sale, SaleItem
from purchases.models import Purchase
from inventory.models import Stock, StockAlert
from products.models import Product


def get_user_org(user):
    """Get user's organization or None for SaaS admin"""
    if hasattr(user, 'organization'):
        return user.organization
    return None


def login_view(request):
    """লগইন পেজ"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'স্বাগতম, {user.get_full_name() or user.username}!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'ভুল ইউজারনেম বা পাসওয়ার্ড!')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """লগআউট"""
    logout(request)
    messages.success(request, 'সফলভাবে লগআউট হয়েছে!')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """ড্যাশবোর্ড - মূল পেজ"""
    org = get_user_org(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # Base querysets filtered by organization
    if org:
        sales_qs = Sale.objects.filter(organization=org)
        purchases_qs = Purchase.objects.filter(organization=org)
        stock_qs = Stock.objects.filter(organization=org)
        alert_qs = StockAlert.objects.filter(organization=org)
        product_qs = Product.objects.filter(organization=org)
    else:
        # SaaS admin sees all
        sales_qs = Sale.objects.all()
        purchases_qs = Purchase.objects.all()
        stock_qs = Stock.objects.all()
        alert_qs = StockAlert.objects.all()
        product_qs = Product.objects.all()
    
    # Today's stats
    today_sales = sales_qs.filter(sale_date__date=today)
    today_total = today_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    today_count = today_sales.count()
    
    # Monthly stats
    monthly_sales = sales_qs.filter(sale_date__date__gte=this_month_start)
    monthly_total = monthly_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Monthly purchases
    monthly_purchases = purchases_qs.filter(purchase_date__date__gte=this_month_start)
    monthly_purchase_total = monthly_purchases.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Calculate profit
    monthly_profit = monthly_total - monthly_purchase_total
    
    # Low stock products
    low_stock_items = stock_qs.filter(quantity__lte=F('reorder_level')).select_related('product')[:10]
    
    # Recent sales
    recent_sales = sales_qs.select_related('customer', 'created_by').order_by('-sale_date')[:10]
    
    # Stock alerts
    unread_alerts = alert_qs.filter(is_read=False).count()
    
    # Total stock value
    total_stock_value = stock_qs.annotate(
        value=F('quantity') * F('product__buying_price')
    ).aggregate(total=Sum('value'))['total'] or Decimal('0')
    
    # Due amounts
    customer_due = sales_qs.filter(payment_status__in=['unpaid', 'partial']).aggregate(
        total=Sum('due_amount'))['total'] or Decimal('0')
    supplier_due = purchases_qs.filter(payment_status__in=['unpaid', 'partial']).aggregate(
        total=Sum('due_amount'))['total'] or Decimal('0')
    
    # Product count
    total_products = product_qs.filter(is_active=True).count()
    
    context = {
        'today_total': today_total,
        'today_count': today_count,
        'monthly_total': monthly_total,
        'monthly_profit': monthly_profit,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
        'unread_alerts': unread_alerts,
        'total_stock_value': total_stock_value,
        'customer_due': customer_due,
        'supplier_due': supplier_due,
        'total_products': total_products,
        'organization': org,
    }
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    """প্রোফাইল পেজ"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.address = request.POST.get('address', '')
        
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        
        user.save()
        messages.success(request, 'প্রোফাইল আপডেট হয়েছে!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html')


@login_required
def user_list(request):
    """ইউজার তালিকা - শুধু নিজের দোকানের ইউজার"""
    org = get_user_org(request.user)
    
    if org:
        # Store admin/staff sees only their store's users
        users = User.objects.filter(organization=org).order_by('-date_joined')
    else:
        # SaaS admin sees all
        users = User.objects.all().order_by('-date_joined')
    
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_add(request):
    """নতুন ইউজার যোগ - নিজের দোকানে"""
    org = get_user_org(request.user)
    
    # Check user limit for organization
    if org and org.plan:
        current_users = User.objects.filter(organization=org).count()
        if current_users >= org.plan.max_users:
            messages.error(request, f'আপনার প্ল্যানে সর্বোচ্চ {org.plan.max_users} জন ইউজার যোগ করতে পারবেন। প্ল্যান আপগ্রেড করুন।')
            return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'staff')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'এই ইউজারনেম ইতিমধ্যে আছে!')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                role=role,
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                organization=org,  # Assign to current user's organization
            )
            messages.success(request, 'নতুন ইউজার তৈরি হয়েছে!')
            return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_form.html')


@login_required
def user_edit(request, pk):
    """ইউজার এডিট - শুধু নিজের দোকানের"""
    org = get_user_org(request.user)
    
    if org:
        user = get_object_or_404(User, pk=pk, organization=org)
    else:
        user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.role = request.POST.get('role', user.role)
        user.is_active = request.POST.get('is_active') == 'on'
        
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        
        user.save()
        messages.success(request, 'ইউজার আপডেট হয়েছে!')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_form.html', {'edit_user': user})
