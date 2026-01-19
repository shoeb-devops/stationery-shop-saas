from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
from .models import Organization, SubscriptionPlan, Subscription
from accounts.models import User


def pricing(request):
    """প্রাইসিং পেজ"""
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, 'tenants/pricing.html', {'plans': plans})


def register(request):
    """নতুন দোকান রেজিস্ট্রেশন"""
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Organization info
        shop_name = request.POST.get('shop_name')
        owner_name = request.POST.get('owner_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address', '')
        
        # User info
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Plan
        plan_id = request.POST.get('plan')
        
        # Validation
        if password != password2:
            messages.error(request, 'পাসওয়ার্ড মিলছে না!')
            return redirect('tenants:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'এই ইউজারনেম আগে থেকে আছে!')
            return redirect('tenants:register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'এই ইমেইল আগে থেকে আছে!')
            return redirect('tenants:register')
        
        # Create slug
        base_slug = slugify(shop_name)
        slug = base_slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Get plan
        plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
        
        # Create Organization
        org = Organization.objects.create(
            name=shop_name,
            slug=slug,
            owner_name=owner_name,
            email=email,
            phone=phone,
            address=address,
            plan=plan,
            is_active=True
        )
        
        # Create Subscription (Free plan gets 1 year, others get 14 days trial)
        if plan.name == 'free':
            end_date = timezone.now() + timedelta(days=365)
            status = 'active'
            is_active = True
        else:
            end_date = timezone.now() + timedelta(days=14)
            status = 'active'
            is_active = True
        
        Subscription.objects.create(
            organization=org,
            plan=plan,
            amount=0,  # Trial/Free
            start_date=timezone.now(),
            end_date=end_date,
            status=status,
            is_active=is_active
        )
        
        # Create User (Owner)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=owner_name,
            phone=phone,
            role='admin',
            organization=org,
            is_owner=True
        )
        
        # Login user
        login(request, user)
        messages.success(request, f'স্বাগতম! আপনার দোকান "{shop_name}" সফলভাবে তৈরি হয়েছে।')
        return redirect('accounts:dashboard')
    
    return render(request, 'tenants/register.html', {'plans': plans})


def shop_settings(request):
    """দোকানের সেটিংস"""
    if not hasattr(request.user, 'organization') or not request.user.organization:
        messages.error(request, 'কোনো দোকান খুঁজে পাওয়া যায়নি!')
        return redirect('accounts:dashboard')
    
    org = request.user.organization
    
    if request.method == 'POST':
        org.name = request.POST.get('name', org.name)
        org.phone = request.POST.get('phone', org.phone)
        org.address = request.POST.get('address', org.address)
        
        if request.FILES.get('logo'):
            org.logo = request.FILES['logo']
        
        org.save()
        messages.success(request, 'সেটিংস আপডেট হয়েছে!')
        return redirect('tenants:settings')
    
    subscription = org.active_subscription
    
    return render(request, 'tenants/settings.html', {
        'organization': org,
        'subscription': subscription
    })


def subscription_details(request):
    """সাবস্ক্রিপশন বিস্তারিত"""
    if not hasattr(request.user, 'organization') or not request.user.organization:
        return redirect('accounts:dashboard')
    
    org = request.user.organization
    subscription = org.active_subscription
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    # Usage stats
    usage = {
        'products': org.get_current_product_count(),
        'products_limit': org.plan.max_products if org.plan else 0,
        'users': org.get_current_user_count(),
        'users_limit': org.plan.max_users if org.plan else 0,
    }
    
    return render(request, 'tenants/subscription.html', {
        'organization': org,
        'subscription': subscription,
        'plans': plans,
        'usage': usage
    })
