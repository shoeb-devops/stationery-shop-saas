from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import Transaction, DailyCashFlow, Expense
from sales.models import Sale
from purchases.models import Purchase


@login_required
def accounting_dashboard(request):
    """অ্যাকাউন্টিং ড্যাশবোর্ড"""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # Monthly income (sales)
    monthly_sales = Sale.objects.filter(
        sale_date__date__gte=this_month_start
    ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Monthly expenses
    monthly_purchases = Purchase.objects.filter(
        purchase_date__date__gte=this_month_start
    ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    monthly_expenses = Expense.objects.filter(
        expense_date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_expense = monthly_purchases + monthly_expenses
    
    # Profit
    monthly_profit = monthly_sales - total_expense
    
    # Receivables (customer dues)
    receivables = Sale.objects.filter(
        payment_status__in=['unpaid', 'partial']
    ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    
    # Payables (supplier dues)
    payables = Purchase.objects.filter(
        payment_status__in=['unpaid', 'partial']
    ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    
    # Recent transactions
    recent_transactions = Transaction.objects.all()[:10]
    
    context = {
        'monthly_sales': monthly_sales,
        'monthly_purchases': monthly_purchases,
        'monthly_expenses': monthly_expenses,
        'monthly_profit': monthly_profit,
        'receivables': receivables,
        'payables': payables,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'accounting/dashboard.html', context)


@login_required
def transaction_list(request):
    """লেনদেন তালিকা"""
    transactions = Transaction.objects.all()
    
    # Filter by type
    trans_type = request.GET.get('type')
    if trans_type:
        transactions = transactions.filter(transaction_type=trans_type)
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        transactions = transactions.filter(category=category)
    
    # Filter by date
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        transactions = transactions.filter(transaction_date__gte=from_date)
    if to_date:
        transactions = transactions.filter(transaction_date__lte=to_date)
    
    return render(request, 'accounting/transaction_list.html', {'transactions': transactions[:100]})


@login_required
def transaction_add(request):
    """নতুন লেনদেন"""
    if request.method == 'POST':
        Transaction.objects.create(
            transaction_type=request.POST.get('type'),
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            description=request.POST.get('description'),
            reference=request.POST.get('reference', ''),
            transaction_date=request.POST.get('date', timezone.now().date()),
            created_by=request.user,
        )
        messages.success(request, 'লেনদেন যোগ হয়েছে!')
        return redirect('accounting:transaction_list')
    
    return render(request, 'accounting/transaction_form.html')


@login_required
def expense_list(request):
    """খরচ তালিকা"""
    expenses = Expense.objects.all()
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category=category)
    
    # Filter by date
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        expenses = expenses.filter(expense_date__gte=from_date)
    if to_date:
        expenses = expenses.filter(expense_date__lte=to_date)
    
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'expenses': expenses[:100],
        'total': total,
    }
    return render(request, 'accounting/expense_list.html', context)


@login_required
def expense_add(request):
    """নতুন খরচ"""
    if request.method == 'POST':
        expense = Expense.objects.create(
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            description=request.POST.get('description', ''),
            expense_date=request.POST.get('date', timezone.now().date()),
            created_by=request.user,
        )
        
        if request.FILES.get('receipt'):
            expense.receipt = request.FILES['receipt']
            expense.save()
        
        messages.success(request, 'খরচ যোগ হয়েছে!')
        return redirect('accounting:expense_list')
    
    return render(request, 'accounting/expense_form.html')


@login_required
def cashflow_list(request):
    """ক্যাশ ফ্লো তালিকা"""
    cashflows = DailyCashFlow.objects.all()[:30]
    return render(request, 'accounting/cashflow_list.html', {'cashflows': cashflows})


@login_required
def today_cashflow(request):
    """আজকের ক্যাশ ফ্লো"""
    today = timezone.now().date()
    
    cashflow, created = DailyCashFlow.objects.get_or_create(
        date=today,
        defaults={
            'opening_balance': Decimal('0'),
            'total_income': Decimal('0'),
            'total_expense': Decimal('0'),
        }
    )
    
    if created or not cashflow.is_closed:
        # Calculate from yesterday's closing
        yesterday = today - timedelta(days=1)
        yesterday_cf = DailyCashFlow.objects.filter(date=yesterday).first()
        if yesterday_cf:
            cashflow.opening_balance = yesterday_cf.closing_balance
        
        # Today's income
        today_sales = Sale.objects.filter(sale_date__date=today)
        cashflow.total_income = today_sales.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
        
        # Today's expenses
        today_purchases = Purchase.objects.filter(purchase_date__date=today)
        purchase_payments = today_purchases.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
        
        today_expenses = Expense.objects.filter(expense_date=today)
        expense_total = today_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        cashflow.total_expense = purchase_payments + expense_total
        cashflow.calculate_closing()
        cashflow.save()
    
    # Today's breakdown
    today_sales = Sale.objects.filter(sale_date__date=today)
    today_purchases = Purchase.objects.filter(purchase_date__date=today)
    today_expenses = Expense.objects.filter(expense_date=today)
    
    context = {
        'cashflow': cashflow,
        'sales': today_sales,
        'purchases': today_purchases,
        'expenses': today_expenses,
    }
    return render(request, 'accounting/today_cashflow.html', context)


@login_required
def profit_loss_report(request):
    """লাভ-ক্ষতি রিপোর্ট"""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if not from_date:
        from_date = timezone.now().date().replace(day=1)
    if not to_date:
        to_date = timezone.now().date()
    
    # Sales
    sales = Sale.objects.filter(
        sale_date__date__gte=from_date,
        sale_date__date__lte=to_date
    )
    total_sales = sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Cost of goods sold (buying price of sold items)
    from sales.models import SaleItem
    sold_items = SaleItem.objects.filter(sale__in=sales)
    cogs = sum(item.quantity * item.product.buying_price for item in sold_items)
    
    # Gross profit
    gross_profit = total_sales - cogs
    
    # Operating expenses
    expenses = Expense.objects.filter(
        expense_date__gte=from_date,
        expense_date__lte=to_date
    )
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Net profit
    net_profit = gross_profit - total_expenses
    
    context = {
        'from_date': from_date,
        'to_date': to_date,
        'total_sales': total_sales,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'expenses_by_category': expenses.values('category').annotate(total=Sum('amount')),
    }
    return render(request, 'accounting/profit_loss.html', context)


@login_required
def income_report(request):
    """আয় রিপোর্ট"""
    from_date = request.GET.get('from_date', timezone.now().date().replace(day=1))
    to_date = request.GET.get('to_date', timezone.now().date())
    
    sales = Sale.objects.filter(
        sale_date__date__gte=from_date,
        sale_date__date__lte=to_date
    ).order_by('-sale_date')
    
    total = sales.aggregate(total=Sum('grand_total'))['total'] or 0
    
    context = {
        'sales': sales,
        'from_date': from_date,
        'to_date': to_date,
        'total': total,
    }
    return render(request, 'accounting/income_report.html', context)


@login_required
def expense_report(request):
    """ব্যয় রিপোর্ট"""
    from_date = request.GET.get('from_date', timezone.now().date().replace(day=1))
    to_date = request.GET.get('to_date', timezone.now().date())
    
    # Purchases
    purchases = Purchase.objects.filter(
        purchase_date__date__gte=from_date,
        purchase_date__date__lte=to_date
    )
    purchase_total = purchases.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    
    # Other expenses
    expenses = Expense.objects.filter(
        expense_date__gte=from_date,
        expense_date__lte=to_date
    )
    expense_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # By category
    expense_by_category = expenses.values('category').annotate(total=Sum('amount'))
    
    context = {
        'from_date': from_date,
        'to_date': to_date,
        'purchase_total': purchase_total,
        'expense_total': expense_total,
        'grand_total': purchase_total + expense_total,
        'expense_by_category': expense_by_category,
        'purchases': purchases,
        'expenses': expenses,
    }
    return render(request, 'accounting/expense_report.html', context)
