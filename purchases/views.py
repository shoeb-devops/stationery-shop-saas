from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal

from .models import Supplier, Purchase, PurchaseItem, SupplierPayment
from products.models import Product
from inventory.models import Stock, StockMovement


@login_required
def purchase_list(request):
    """ক্রয় তালিকা"""
    purchases = Purchase.objects.select_related('supplier', 'created_by').all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        purchases = purchases.filter(payment_status=status)
    
    # Filter by date
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        purchases = purchases.filter(purchase_date__date__gte=from_date)
    if to_date:
        purchases = purchases.filter(purchase_date__date__lte=to_date)
    
    context = {
        'purchases': purchases[:100],
    }
    return render(request, 'purchases/purchase_list.html', context)


@login_required
def purchase_add(request):
    """নতুন ক্রয়"""
    if request.method == 'POST':
        # Create purchase
        purchase = Purchase.objects.create(
            supplier_id=request.POST.get('supplier') or None,
            discount_amount=request.POST.get('discount', 0) or 0,
            shipping_cost=request.POST.get('shipping', 0) or 0,
            paid_amount=request.POST.get('paid_amount', 0) or 0,
            payment_method=request.POST.get('payment_method', 'cash'),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        
        # Add items
        subtotal = 0
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        
        for i, product_id in enumerate(product_ids):
            if product_id:
                product = Product.objects.get(pk=product_id)
                quantity = Decimal(quantities[i])
                price = Decimal(prices[i])
                
                PurchaseItem.objects.create(
                    purchase=purchase,
                    product=product,
                    quantity=quantity,
                    unit_price=price,
                    total=quantity * price,
                )
                subtotal += quantity * price
                
                # Update stock
                stock, created = Stock.objects.get_or_create(
                    product=product,
                    defaults={'quantity': 0, 'reorder_level': 10}
                )
                previous_qty = stock.quantity
                stock.quantity += quantity
                stock.save()
                
                StockMovement.objects.create(
                    product=product,
                    movement_type='in',
                    quantity=quantity,
                    previous_quantity=previous_qty,
                    new_quantity=stock.quantity,
                    reference=purchase.purchase_number,
                    notes=f'ক্রয়: {purchase.purchase_number}',
                    created_by=request.user,
                )
        
        # Update purchase totals
        purchase.subtotal = subtotal
        purchase.grand_total = subtotal - Decimal(str(purchase.discount_amount)) + Decimal(str(purchase.shipping_cost))
        purchase.save()
        
        messages.success(request, f'ক্রয় সফল! নম্বর: {purchase.purchase_number}')
        return redirect('purchases:purchase_detail', pk=purchase.pk)
    
    products = Product.objects.filter(is_active=True).select_related('stock', 'unit')
    suppliers = Supplier.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'suppliers': suppliers,
    }
    return render(request, 'purchases/purchase_form.html', context)


@login_required
def purchase_detail(request, pk):
    """ক্রয় বিস্তারিত"""
    purchase = get_object_or_404(Purchase, pk=pk)
    items = purchase.items.select_related('product')
    
    context = {
        'purchase': purchase,
        'items': items,
    }
    return render(request, 'purchases/purchase_detail.html', context)


@login_required
def add_payment(request, pk):
    """সাপ্লায়ার পেমেন্ট"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        
        SupplierPayment.objects.create(
            purchase=purchase,
            amount=amount,
            payment_method=request.POST.get('payment_method', 'cash'),
            reference=request.POST.get('reference', ''),
            notes=request.POST.get('notes', ''),
            paid_by=request.user,
        )
        
        # Update purchase
        purchase.paid_amount += amount
        purchase.save()
        
        messages.success(request, f'{amount}৳ পেমেন্ট করা হয়েছে!')
    
    return redirect('purchases:purchase_detail', pk=pk)


@login_required
def supplier_list(request):
    """সাপ্লায়ার তালিকা"""
    suppliers = Supplier.objects.all()
    return render(request, 'purchases/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_add(request):
    """নতুন সাপ্লায়ার"""
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            company=request.POST.get('company', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
        )
        messages.success(request, 'সাপ্লায়ার যোগ হয়েছে!')
        return redirect('purchases:supplier_list')
    return render(request, 'purchases/supplier_form.html')


@login_required
def supplier_detail(request, pk):
    """সাপ্লায়ার বিস্তারিত"""
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = supplier.purchases.all()[:20]
    
    context = {
        'supplier': supplier,
        'purchases': purchases,
    }
    return render(request, 'purchases/supplier_detail.html', context)


@login_required
def purchase_report(request):
    """ক্রয় রিপোর্ট"""
    from_date = request.GET.get('from_date', timezone.now().date().replace(day=1))
    to_date = request.GET.get('to_date', timezone.now().date())
    
    purchases = Purchase.objects.filter(
        purchase_date__date__gte=from_date,
        purchase_date__date__lte=to_date
    ).select_related('supplier')
    
    total_purchases = purchases.aggregate(total=Sum('grand_total'))['total'] or 0
    total_paid = purchases.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_due = purchases.aggregate(total=Sum('due_amount'))['total'] or 0
    
    context = {
        'purchases': purchases,
        'from_date': from_date,
        'to_date': to_date,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    return render(request, 'purchases/report.html', context)


@login_required
def supplier_due_report(request):
    """সাপ্লায়ার বাকি রিপোর্ট"""
    purchases = Purchase.objects.filter(
        payment_status__in=['unpaid', 'partial']
    ).select_related('supplier').order_by('-due_amount')
    
    total_due = purchases.aggregate(total=Sum('due_amount'))['total'] or 0
    
    context = {
        'purchases': purchases,
        'total_due': total_due,
    }
    return render(request, 'purchases/due_report.html', context)
