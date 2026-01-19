from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, F

from .models import Stock, StockMovement, StockAlert
from products.models import Product


@login_required
def stock_list(request):
    """স্টক তালিকা"""
    stocks = Stock.objects.select_related('product', 'product__category', 'product__unit').all()
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        stocks = stocks.filter(product__category_id=category_id)
    
    # Calculate totals
    total_value = stocks.aggregate(
        total=Sum(F('quantity') * F('product__buying_price'))
    )['total'] or 0
    
    total_selling_value = stocks.aggregate(
        total=Sum(F('quantity') * F('product__selling_price'))
    )['total'] or 0
    
    from products.models import Category
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'stocks': stocks,
        'categories': categories,
        'total_value': total_value,
        'total_selling_value': total_selling_value,
    }
    return render(request, 'inventory/stock_list.html', context)


@login_required
def low_stock(request):
    """লো স্টক তালিকা"""
    stocks = Stock.objects.filter(
        quantity__lte=F('reorder_level')
    ).select_related('product', 'product__category')
    
    return render(request, 'inventory/low_stock.html', {'stocks': stocks})


@login_required
def movement_list(request):
    """স্টক মুভমেন্ট হিস্ট্রি"""
    movements = StockMovement.objects.select_related('product', 'created_by').all()
    
    # Filter by type
    movement_type = request.GET.get('type')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    # Filter by date
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        movements = movements.filter(created_at__date__gte=from_date)
    if to_date:
        movements = movements.filter(created_at__date__lte=to_date)
    
    return render(request, 'inventory/movement_list.html', {'movements': movements[:100]})


@login_required
def stock_adjust(request, pk):
    """স্টক সমন্বয়"""
    stock = get_object_or_404(Stock, pk=pk)
    
    if request.method == 'POST':
        adjustment_type = request.POST.get('type')
        quantity = float(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        previous_qty = stock.quantity
        
        if adjustment_type == 'add':
            stock.quantity += quantity
            movement_type = 'in'
        elif adjustment_type == 'remove':
            stock.quantity -= quantity
            movement_type = 'out'
        else:  # set
            stock.quantity = quantity
            movement_type = 'adjustment'
        
        stock.save()
        
        # Create movement record
        StockMovement.objects.create(
            product=stock.product,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=previous_qty,
            new_quantity=stock.quantity,
            notes=notes,
            created_by=request.user,
        )
        
        messages.success(request, 'স্টক আপডেট হয়েছে!')
        return redirect('inventory:stock_list')
    
    return render(request, 'inventory/stock_adjust.html', {'stock': stock})


@login_required
def alerts(request):
    """স্টক অ্যালার্ট"""
    alerts = StockAlert.objects.select_related('stock', 'stock__product').all()
    
    if request.method == 'POST':
        # Mark all as read
        alerts.update(is_read=True)
        messages.success(request, 'সব অ্যালার্ট পড়া হয়েছে!')
        return redirect('inventory:alerts')
    
    return render(request, 'inventory/alerts.html', {'alerts': alerts})


@login_required
def inventory_report(request):
    """ইনভেন্টরি রিপোর্ট"""
    stocks = Stock.objects.select_related('product', 'product__category').all()
    
    # Group by category
    from products.models import Category
    categories = Category.objects.filter(is_active=True)
    
    category_data = []
    for cat in categories:
        cat_stocks = stocks.filter(product__category=cat)
        total_value = cat_stocks.aggregate(
            total=Sum(F('quantity') * F('product__buying_price'))
        )['total'] or 0
        category_data.append({
            'category': cat,
            'count': cat_stocks.count(),
            'total_value': total_value,
        })
    
    total_stock_value = stocks.aggregate(
        total=Sum(F('quantity') * F('product__buying_price'))
    )['total'] or 0
    
    context = {
        'category_data': category_data,
        'total_stock_value': total_stock_value,
        'total_products': stocks.count(),
    }
    return render(request, 'inventory/report.html', context)
