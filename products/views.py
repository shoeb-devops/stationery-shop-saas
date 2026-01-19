from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

from .models import Category, GSMType, PaperSize, Unit, Product
from inventory.models import Stock


@login_required
def product_list(request):
    """পণ্য তালিকা"""
    products = Product.objects.filter(is_active=True).select_related('category', 'gsm', 'size', 'unit')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) |
            Q(barcode__icontains=search)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by GSM
    gsm_id = request.GET.get('gsm')
    if gsm_id:
        products = products.filter(gsm_id=gsm_id)
    
    categories = Category.objects.filter(is_active=True)
    gsm_types = GSMType.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'gsm_types': gsm_types,
        'search': search,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_add(request):
    """নতুন পণ্য যোগ"""
    if request.method == 'POST':
        product = Product.objects.create(
            name=request.POST.get('name'),
            category_id=request.POST.get('category') or None,
            gsm_id=request.POST.get('gsm') or None,
            size_id=request.POST.get('size') or None,
            unit_id=request.POST.get('unit') or None,
            buying_price=request.POST.get('buying_price', 0),
            selling_price=request.POST.get('selling_price', 0),
            barcode=request.POST.get('barcode', ''),
            description=request.POST.get('description', ''),
        )
        
        if request.FILES.get('image'):
            product.image = request.FILES['image']
            product.save()
        
        # Create stock entry
        Stock.objects.create(
            product=product,
            quantity=request.POST.get('initial_stock', 0),
            reorder_level=request.POST.get('reorder_level', 10),
        )
        
        messages.success(request, f'পণ্য "{product.name}" সফলভাবে যোগ হয়েছে!')
        return redirect('products:product_list')
    
    context = {
        'categories': Category.objects.filter(is_active=True),
        'gsm_types': GSMType.objects.all(),
        'sizes': PaperSize.objects.all(),
        'units': Unit.objects.all(),
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_detail(request, pk):
    """পণ্য বিস্তারিত"""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


@login_required
def product_edit(request, pk):
    """পণ্য সম্পাদনা"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category') or None
        product.gsm_id = request.POST.get('gsm') or None
        product.size_id = request.POST.get('size') or None
        product.unit_id = request.POST.get('unit') or None
        product.buying_price = request.POST.get('buying_price', 0)
        product.selling_price = request.POST.get('selling_price', 0)
        product.barcode = request.POST.get('barcode', '')
        product.description = request.POST.get('description', '')
        
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        
        product.save()
        
        # Update stock reorder level
        if hasattr(product, 'stock'):
            product.stock.reorder_level = request.POST.get('reorder_level', 10)
            product.stock.save()
        
        messages.success(request, 'পণ্য আপডেট হয়েছে!')
        return redirect('products:product_list')
    
    context = {
        'product': product,
        'categories': Category.objects.filter(is_active=True),
        'gsm_types': GSMType.objects.all(),
        'sizes': PaperSize.objects.all(),
        'units': Unit.objects.all(),
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, pk):
    """পণ্য মুছুন"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, 'পণ্য মুছে ফেলা হয়েছে!')
    return redirect('products:product_list')


@login_required
def category_list(request):
    """ক্যাটাগরি তালিকা"""
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})


@login_required
def category_add(request):
    """নতুন ক্যাটাগরি"""
    if request.method == 'POST':
        Category.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
        )
        messages.success(request, 'ক্যাটাগরি যোগ হয়েছে!')
        return redirect('products:category_list')
    return render(request, 'products/category_form.html')


@login_required
def gsm_list(request):
    """GSM টাইপ তালিকা"""
    if request.method == 'POST':
        GSMType.objects.create(
            value=request.POST.get('value'),
            description=request.POST.get('description', ''),
        )
        messages.success(request, 'GSM টাইপ যোগ হয়েছে!')
    
    gsm_types = GSMType.objects.all()
    return render(request, 'products/gsm_list.html', {'gsm_types': gsm_types})


@login_required
def product_search(request):
    """পণ্য সার্চ API"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query),
        is_active=True
    ).select_related('stock', 'unit')[:20]
    
    data = []
    for p in products:
        stock_qty = p.stock.quantity if hasattr(p, 'stock') else 0
        data.append({
            'id': p.id,
            'name': str(p),
            'sku': p.sku,
            'price': float(p.selling_price),
            'buying_price': float(p.buying_price),
            'stock': float(stock_qty),
            'unit': p.unit.short_name if p.unit else 'পিস',
        })
    
    return JsonResponse({'products': data})


@login_required
def product_api(request, pk):
    """পণ্য API"""
    product = get_object_or_404(Product, pk=pk)
    stock_qty = product.stock.quantity if hasattr(product, 'stock') else 0
    
    data = {
        'id': product.id,
        'name': str(product),
        'sku': product.sku,
        'price': float(product.selling_price),
        'buying_price': float(product.buying_price),
        'stock': float(stock_qty),
        'unit': product.unit.short_name if product.unit else 'পিস',
    }
    return JsonResponse(data)
