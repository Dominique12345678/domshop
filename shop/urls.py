from django.urls import path
from . import views
from .views import confirm_order, invoice
app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),  # Global name to fix NoReverseMatch
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('auth/login/', views.custom_login, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register, name='register'),

    path('admin/categories/manage/', views.category_manage, name='category_manage'),

    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    path('panier/', views.view_cart, name='view_cart'),
    path('panier/retirer/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    
    path('admin/products/manage/', views.product_manage, name='product_manage'),
    path('produits/', views.product_list_client, name='product_list_client'),
    path('panier/commande/', confirm_order, name='confirm_order'),
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('panier/facture/<int:order_id>/', invoice, name='invoice'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('invoice/<int:order_id>/download/html/', views.download_invoice_html, name='download_invoice_html'),
    path('invoice/<int:order_id>/download/pdf/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('admin/invoices/', views.admin_invoices, name='admin_invoices'),
    path('admin/invoices/<int:order_id>/', views.admin_invoice_detail, name='admin_invoice_detail'),
    path('admin/stock/', views.admin_stock, name='admin_stock'),
]


