from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json

from .models import Customer, Sale, SaleItem, Payment
from products.models import Product
from inventory.models import Stock, StockMovement


@login_required
def sale_list(request):
    """বিক্রয় তালিকা"""
    sales = Sale.objects.select_related('customer', 'created_by').all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        sales = sales.filter(payment_status=status)
    
    # Filter by date
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        sales = sales.filter(sale_date__date__gte=from_date)
    if to_date:
        sales = sales.filter(sale_date__date__lte=to_date)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        sales = sales.filter(
            Q(invoice_number__icontains=search) |
            Q(customer__name__icontains=search)
        )
    
    context = {
        'sales': sales[:100],
        'search': search,
    }
    return render(request, 'sales/sale_list.html', context)


@login_required
def pos(request):
    """POS - Point of Sale"""
    products = Product.objects.filter(is_active=True).select_related('stock', 'unit')[:50]
    customers = Customer.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'customers': customers,
    }
    return render(request, 'sales/pos.html', context)


@login_required
def sale_add(request):
    """নতুন বিক্রয়"""
    if request.method == 'POST':
        # Create sale
        sale = Sale.objects.create(
            customer_id=request.POST.get('customer') or None,
            discount_amount=request.POST.get('discount', 0) or 0,
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
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=price,
                    total=quantity * price,
                )
                subtotal += quantity * price
                
                # Update stock
                if hasattr(product, 'stock'):
                    previous_qty = product.stock.quantity
                    product.stock.quantity -= quantity
                    product.stock.save()
                    
                    StockMovement.objects.create(
                        product=product,
                        movement_type='out',
                        quantity=quantity,
                        previous_quantity=previous_qty,
                        new_quantity=product.stock.quantity,
                        reference=sale.invoice_number,
                        notes=f'বিক্রয়: {sale.invoice_number}',
                        created_by=request.user,
                    )
        
        # Update sale totals
        sale.subtotal = subtotal
        sale.grand_total = subtotal - sale.discount_amount
        sale.save()
        
        messages.success(request, f'বিক্রয় সফল! ইনভয়েস: {sale.invoice_number}')
        return redirect('sales:sale_detail', pk=sale.pk)
    
    products = Product.objects.filter(is_active=True).select_related('stock', 'unit')
    customers = Customer.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'customers': customers,
    }
    return render(request, 'sales/sale_form.html', context)


@login_required
@csrf_exempt
def create_sale_api(request):
    """POS থেকে বিক্রয় তৈরি API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        data = json.loads(request.body)
        
        # Create sale
        sale = Sale.objects.create(
            customer_id=data.get('customer_id') or None,
            discount_amount=Decimal(str(data.get('discount', 0))),
            paid_amount=Decimal(str(data.get('paid_amount', 0))),
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes', ''),
            created_by=request.user,
        )
        
        # Add items
        subtotal = Decimal('0')
        for item in data.get('items', []):
            product = Product.objects.get(pk=item['product_id'])
            quantity = Decimal(str(item['quantity']))
            price = Decimal(str(item['price']))
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=price,
                total=quantity * price,
            )
            subtotal += quantity * price
            
            # Update stock
            if hasattr(product, 'stock'):
                previous_qty = product.stock.quantity
                product.stock.quantity -= quantity
                product.stock.save()
                
                StockMovement.objects.create(
                    product=product,
                    movement_type='out',
                    quantity=quantity,
                    previous_quantity=previous_qty,
                    new_quantity=product.stock.quantity,
                    reference=sale.invoice_number,
                    notes=f'বিক্রয়: {sale.invoice_number}',
                    created_by=request.user,
                )
        
        # Update totals
        sale.subtotal = subtotal
        sale.grand_total = subtotal - sale.discount_amount
        sale.save()
        
        return JsonResponse({
            'success': True,
            'invoice_number': sale.invoice_number,
            'sale_id': sale.pk,
            'grand_total': float(sale.grand_total),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def sale_detail(request, pk):
    """বিক্রয় বিস্তারিত"""
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.select_related('product')
    
    context = {
        'sale': sale,
        'items': items,
    }
    return render(request, 'sales/sale_detail.html', context)


@login_required
def sale_invoice(request, pk):
    """ইনভয়েস প্রিন্ট"""
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.select_related('product')
    
    context = {
        'sale': sale,
        'items': items,
    }
    return render(request, 'sales/invoice.html', context)


@login_required
def add_payment(request, pk):
    """পেমেন্ট যোগ"""
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        
        Payment.objects.create(
            sale=sale,
            amount=amount,
            payment_method=request.POST.get('payment_method', 'cash'),
            reference=request.POST.get('reference', ''),
            notes=request.POST.get('notes', ''),
            received_by=request.user,
        )
        
        # Update sale
        sale.paid_amount += amount
        sale.save()
        
        messages.success(request, f'{amount}৳ পেমেন্ট যোগ হয়েছে!')
    
    return redirect('sales:sale_detail', pk=pk)


@login_required
def customer_list(request):
    """গ্রাহক তালিকা"""
    customers = Customer.objects.all()
    return render(request, 'sales/customer_list.html', {'customers': customers})


@login_required
def customer_add(request):
    """নতুন গ্রাহক"""
    if request.method == 'POST':
        Customer.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            company=request.POST.get('company', ''),
        )
        messages.success(request, 'গ্রাহক যোগ হয়েছে!')
        return redirect('sales:customer_list')
    return render(request, 'sales/customer_form.html')


@login_required
def customer_detail(request, pk):
    """গ্রাহক বিস্তারিত"""
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.all()[:20]
    
    context = {
        'customer': customer,
        'sales': sales,
    }
    return render(request, 'sales/customer_detail.html', context)


@login_required
def daily_sales_report(request):
    """দৈনিক বিক্রয় রিপোর্ট"""
    from_date = request.GET.get('from_date', timezone.now().date())
    to_date = request.GET.get('to_date', timezone.now().date())
    
    sales = Sale.objects.filter(
        sale_date__date__gte=from_date,
        sale_date__date__lte=to_date
    ).select_related('customer', 'created_by')
    
    total_sales = sales.aggregate(total=Sum('grand_total'))['total'] or 0
    total_paid = sales.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_due = sales.aggregate(total=Sum('due_amount'))['total'] or 0
    
    context = {
        'sales': sales,
        'from_date': from_date,
        'to_date': to_date,
        'total_sales': total_sales,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    return render(request, 'sales/daily_report.html', context)


@login_required
def due_report(request):
    """বাকি রিপোর্ট"""
    sales = Sale.objects.filter(
        payment_status__in=['unpaid', 'partial']
    ).select_related('customer').order_by('-due_amount')
    
    total_due = sales.aggregate(total=Sum('due_amount'))['total'] or 0
    
    context = {
        'sales': sales,
        'total_due': total_due,
    }
    return render(request, 'sales/due_report.html', context)
