# POS/admin.py
from django.contrib import admin
from .models import Category, Supplier, Product, Transaction, TransactionItem

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock_quantity', 'category', 'supplier', 'is_low_stock')
    list_filter = ('category', 'supplier')
    search_fields = ('name',)

class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment_method', 'customer_name', 'total_amount', 'is_paid', 'timestamp')
    list_filter = ('payment_method', 'is_paid', 'timestamp')
    search_fields = ('customer_name', 'reference_number')
    inlines = [TransactionItemInline]