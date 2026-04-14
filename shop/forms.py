from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Category, Product, Coupon

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "form-control"}),
        strip=False,
    )

    class Meta:
        model = User
        fields = ('email', 'firstname', 'lastname')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'firstname': forms.TextInput(attrs={'class': 'form-control'}),
            'lastname': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['cat_name']
        labels = {
            'cat_name': 'Nom de la catégorie'
        }
        widgets = {
            'cat_name': forms.TextInput(attrs={'class': 'form-control'})
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['pro_name', 'pro_price', 'pro_desc', 'category', 'photo', 'stock']

        widgets = {
            'pro_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'pro_desc': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3}),
            'pro_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stock'}),
        }

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_percent', 'discount_amount', 'valid_from', 'valid_to', 'active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: SUMMER20'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'En %'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'En FCFA'}),
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
