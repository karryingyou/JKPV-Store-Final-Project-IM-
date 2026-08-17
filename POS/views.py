from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction as db_transaction
from django.utils import timezone
from django.db.models import Sum
from .models import Product, Category, Supplier, Transaction, TransactionItem


LOW_STOCK_THRESHOLD = 5

def home(request):
    """Landing page that routes anonymous users to the login screen and authenticated users to the dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required

def dashboard(request):
    """Renders main POS Dashboard with products, categories, and low stock warnings."""
    products = Product.objects.select_related('category', 'supplier').all()
    categories = Category.objects.all()
    low_stock_products = Product.objects.filter(stock_quantity__lte=LOW_STOCK_THRESHOLD)

    # Today's sales summary
    today = timezone.localtime(timezone.now()).date()
    todays_transactions = Transaction.objects.filter(timestamp__date=today)
    today_total = todays_transactions.aggregate(total=Sum('total_amount'))['total'] or 0
    today_count = todays_transactions.count()

    # Recent transactions (last 6)
    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:6]

    # Top selling products (by quantity)
    top_sellers = (
        TransactionItem.objects.values('product_name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:6]
    )
    
    context = {
        'products': products,
        'categories': categories,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_products.count(),
        'today_total': float(today_total),
        'today_count': today_count,
        'recent_transactions': recent_transactions,
        'top_sellers': top_sellers,
    }
    return render(request, 'POS/dashboard.html', context)


@login_required
def inventory(request):
    """Displays product inventory list with low stock items identified."""
    products = Product.objects.select_related('category', 'supplier').all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    low_stock_count = Product.objects.filter(stock_quantity__lte=LOW_STOCK_THRESHOLD).count()
    
    for product in products:
        product.is_low_stock = product.stock_quantity <= LOW_STOCK_THRESHOLD

    context = {
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'POS/inventory.html', context)


@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock_quantity')
        category_name = request.POST.get('category_name') or request.POST.get('category')
        supplier_name = request.POST.get('supplier_name')

        category = None
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name.strip())

        supplier = None
        if supplier_name:
            supplier, _ = Supplier.objects.get_or_create(name=supplier_name.strip())

        Product.objects.create(
            name=name,
            price=price,
            stock_quantity=stock,
            category=category,
            supplier=supplier
        )
        return redirect('inventory')
    
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    return render(request, 'POS/add_product.html', {'categories': categories, 'suppliers': suppliers})


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock_quantity = request.POST.get('stock_quantity')
        
        category_name = request.POST.get('category_name') or request.POST.get('category')
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name.strip())
            product.category = category
        else:
            product.category = None

        supplier_name = request.POST.get('supplier_name')
        if supplier_name:
            supplier, _ = Supplier.objects.get_or_create(name=supplier_name.strip())
            product.supplier = supplier
        else:
            product.supplier = None

        product.save()
        return redirect('inventory')

    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    return render(request, 'POS/edit_product.html', {'product': product, 'categories': categories, 'suppliers': suppliers})


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('inventory')


@login_required
@require_POST
def restock_product(request, product_id):
    """Quickly adds stock quantity to an existing product."""
    try:
        data = json.loads(request.body)
        add_quantity = int(data.get('quantity', 0))

        if add_quantity <= 0:
            return JsonResponse({'status': 'error', 'message': 'Quantity must be greater than zero.'}, status=400)

        product = get_object_or_404(Product, id=product_id)
        product.stock_quantity += add_quantity
        product.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Added {add_quantity} units to {product.name}. New total: {product.stock_quantity}',
            'new_stock': product.stock_quantity
        })
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid quantity entered.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def record_sale(request):
    try:
        data = json.loads(request.body)
        # Debug logging (can be removed in production)
        # print("INCOMING DATA FROM JS:", data)

        payment_method = data.get('payment_method')
        customer_name = data.get('customer_name', '').strip()
        reference_number = data.get('reference_number', '').strip()

        total = data.get('total', 0)
        items = data.get('items', [])

        if not items:
            return JsonResponse({'status': 'error', 'message': 'Cart is empty.'}, status=400)

        is_paid = False if payment_method == 'Utang' else True

        with db_transaction.atomic():
            new_transaction = Transaction.objects.create(
                payment_method=payment_method,
                customer_name=customer_name,
                reference_number=reference_number if payment_method == 'Gcash' else None,
                total_amount=total,
                is_paid=is_paid
            )

            for item in items:
                product = Product.objects.filter(name=item['name']).first()
                if product:
                    if product.stock_quantity < item['quantity']:
                        raise ValueError(f"Insufficient stock for {product.name}")
                    product.stock_quantity -= item['quantity']
                    product.save()

                TransactionItem.objects.create(
                    transaction=new_transaction,
                    product_name=item['name'],
                    price=item['price'],
                    quantity=item['quantity']
                )

        return JsonResponse({'status': 'success', 'message': 'Sale recorded successfully!'})

    except ValueError as ve:
        return JsonResponse({'status': 'error', 'message': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'System error processing transaction.'}, status=500)


@login_required
def sales_report(request):
    transactions = Transaction.objects.all().order_by('-timestamp')
    daily_sales_dict = {}
    
    for txn in transactions:
        if txn.payment_method == 'Utang' and not txn.is_paid:
            continue
            
        if txn.payment_method == 'Utang' and txn.is_paid and txn.date_paid:
            local_time = timezone.localtime(txn.date_paid)
        else:
            local_time = timezone.localtime(txn.timestamp)
            
        date_key = local_time.date()
        
        if date_key not in daily_sales_dict:
            daily_sales_dict[date_key] = 0
            
        daily_sales_dict[date_key] += float(txn.total_amount)
        
    daily_sales = [
        {'date': date, 'total_sales': "{:.2f}".format(total)}
        for date, total in sorted(daily_sales_dict.items(), key=lambda x: x[0], reverse=True)
    ]
    
    return render(request, 'POS/sales_report.html', {'transactions': transactions, 'daily_sales': daily_sales})


@login_required
def get_utang_records(request):
    utang_transactions = Transaction.objects.filter(payment_method='Utang', is_paid=False).order_by('-timestamp')
    grouped_records = {}
    
    for txn in utang_transactions:
        local_time = timezone.localtime(txn.timestamp)
        date_key = local_time.strftime('%B %d, %Y')
        
        if date_key not in grouped_records:
            grouped_records[date_key] = []

        grouped_records[date_key].append({
            'id': txn.id,
            'customer_name': txn.customer_name if txn.customer_name else 'Unknown Customer',
            'items_summary': txn.items_summary,  
            'amount': float(txn.total_amount)
        })

    return JsonResponse(grouped_records)


@login_required
@csrf_exempt
@require_POST
def mark_utang_paid(request, transaction_id):
    try:
        txn = get_object_or_404(Transaction, id=transaction_id, payment_method='Utang')
        txn.is_paid = True
        txn.date_paid = timezone.now()
        txn.save()
        return JsonResponse({'status': 'success', 'message': 'Debt marked as paid!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)