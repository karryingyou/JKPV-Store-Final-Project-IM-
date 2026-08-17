from django.contrib import admin
from django.urls import path, include
from POS import views

urlpatterns = [
    # RESTORED: Django Admin panel route
    path('admin/', admin.site.urls),
    
    # Django Auth URLs (Login, Password Reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # App URLs
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('inventory/', views.inventory, name='inventory'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('record-sale/', views.record_sale, name='record_sale'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('api/utang-records/', views.get_utang_records, name='get_utang_records'),
    path('mark_utang_paid/<int:transaction_id>/', views.mark_utang_paid, name='mark_utang_paid'),
    path('inventory/restock/<int:product_id>/', views.restock_product, name='restock_product'),
]