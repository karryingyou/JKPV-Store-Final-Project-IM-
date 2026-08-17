from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    category_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'category-list',
            'placeholder': 'Type or select category...'
        })
    )
    supplier_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'supplier-list',
            'placeholder': 'Type or select supplier...'
        })
    )

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock_quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Wilkins Pure Purified Water'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }