from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST 
from .forms import ProductForm
from .models import User, Role, Product, Category
from .forms import CustomUserCreationForm, CategoryForm
from .models import User, Role, Product, Category, CartItem, Order, OrderItem
import json
from django.template.loader import get_template
from django.http import HttpResponse
import tempfile
from xhtml2pdf import pisa
from django.conf import settings
import os



# Vérification rôle admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role.role_name == 'admin')


# Accueil client
def home(request):
    featured_products = Product.objects.all().order_by('-id')[:3]
    return render(request, 'client/home.html', {'featured_products': featured_products})


# Tableau de bord admin
@user_passes_test(is_admin, login_url='shop:login')
def admin_dashboard(request):
    try:
        import json
        from django.db.models import Sum
        user_count = User.objects.count()
        product_count = Product.objects.count()
        category_count = Category.objects.count()
        
        # Statistiques métiers
        orders = Order.objects.order_by('-created_at')
        total_sales = sum(order.total for order in orders)
        recent_orders = orders[:5]
        
        # Données de graphique simples
        labels = [order.created_at.strftime('%d/%m') for order in orders[:10]]
        data = [float(order.total) for order in orders[:10]]
        labels.reverse()
        data.reverse()
        
        return render(request, 'admin/dashboard.html', {
            'user_count': user_count,
            'product_count': product_count,
            'category_count': category_count,
            'total_sales': total_sales,
            'recent_orders': recent_orders,
            'chart_labels': json.dumps(labels),
            'chart_data': json.dumps(data),
        })
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('shop:home')


# Connexion personnalisée
@csrf_protect
def custom_login(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.user.is_authenticated:
        if next_url:
            return redirect(next_url)
        if request.user.role.role_name == 'admin' or request.user.is_superuser:
            return redirect('shop:admin_dashboard')
        return redirect('shop:product_list_client')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, "Veuillez saisir votre email et mot de passe.")
            return render(request, 'client/authentification/login.html')

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, "Compte inactif. Contactez l'administrateur.")
                return render(request, 'client/authentification/login.html')

            login(request, user)

            if next_url:
                return redirect(next_url)

            if user.role.role_name == 'admin' or user.is_superuser:
                return redirect('shop:admin_dashboard')
            else:
                return redirect('shop:product_list_client')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'client/authentification/login.html')


# Déconnexion
def logout_view(request):
    logout(request)
    return redirect('shop:home')


# Inscription utilisateur
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            client_role, created = Role.objects.get_or_create(role_name='client')
            user.role = client_role
            user.save()
            
            messages.success(request, "Inscription réussie. Vous pouvez maintenant vous connecter.")
            return redirect('shop:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'client/authentification/register.html', {'form': form})


@user_passes_test(is_admin, login_url='shop:login')
def category_manage(request):
    # Rechercher
    search_query = request.GET.get('search', '')
    categories = Category.objects.filter(cat_name__icontains=search_query)

    selected_category = None
    form = CategoryForm()

    # Modifier (préremplissage)
    if 'edit' in request.GET:
        selected_category = get_object_or_404(Category, id=request.GET['edit'])
        form = CategoryForm(instance=selected_category)

    # Création ou mise à jour
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            category_to_delete = get_object_or_404(Category, id=request.POST['delete_id'])
            category_to_delete.delete()
            messages.success(request, "Catégorie supprimée.")
            return redirect('shop:category_manage')

        category_id = request.POST.get('category_id')
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            form = CategoryForm(request.POST, instance=category)
        else:
            form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            if category_id:
                messages.success(request, "Catégorie mise à jour.")
            else:
                messages.success(request, "Catégorie créée.")
            return redirect('shop:category_manage')

    return render(request, 'admin/categories/manage.html', {
        'form': form,
        'categories': categories,
        'selected_category': selected_category,
    })


# Gestion des produits


@user_passes_test(is_admin, login_url='shop:login')
def product_manage(request):
    query = request.GET.get('q', '')
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(pro_name__icontains=query) |
            Q(pro_desc__icontains=query) |
            Q(category__cat_name__icontains=query)
        )

    if request.method == 'POST':
        if 'product_id' in request.POST and request.POST['product_id']:
            product = get_object_or_404(Product, pk=request.POST['product_id'])
            form = ProductForm(request.POST, request.FILES, instance=product)
        else:
            form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            messages.success(request, "Produit sauvegardé avec succès.")
            return redirect('shop:product_manage')
    else:
        form = ProductForm()

    # Suppression
    if request.method == 'GET' and 'delete' in request.GET:
        product_to_delete = get_object_or_404(Product, pk=request.GET['delete'])
        product_to_delete.delete()
        messages.success(request, "Produit supprimé avec succès.")
        return redirect('shop:product_manage')

    # Récupération des catégories pour la liste déroulante
    categories = Category.objects.all()

    context = {
        'products': products,
        'form': form,
        'query': query,
        'categories': categories,  # <-- ici on ajoute
    }
    return render(request, 'admin/products/manage.html', context)




@login_required
def product_list_client(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(pro_name__icontains=query) | 
            Q(pro_desc__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.all()
    cart_items = CartItem.objects.filter(user=request.user).values_list('product_id', flat=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('client/products/product_grid.html', {
            'products': products, 
            'cart_items': cart_items, 
            'request': request
        })
        return JsonResponse({'html': html})

    return render(request, 'client/products/list.html', {
        'products': products,
        'categories': categories,
        'cart_items': cart_items
    })


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Vérifie si le produit est déjà dans le panier
    if CartItem.objects.filter(user=request.user, product=product).exists():
        msg = f"« {product.pro_name} » est déjà dans votre panier."
        status = 'info'
    else:
        CartItem.objects.create(user=request.user, product=product, quantity=1)
        msg = f"« {product.pro_name} » a été ajouté au panier."
        status = 'success'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': status, 'message': msg})

    if status == 'info':
        messages.info(request, msg)
    else:
        messages.success(request, msg)

    return redirect('shop:product_list_client')


@login_required
def view_cart(request):
    items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in items)
    return render(request, 'client/cart/view.html', {'items': items, 'total': total})

@require_POST
@login_required
def update_cart(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        if quantity < 1:
            raise ValueError("Quantité invalide.")

        # Correction : suppression de 'cart__user' → on filtre directement sur user
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        cart_item.quantity = quantity
        cart_item.save()

        # Recalcul du total
        total = sum(item.total_price() for item in CartItem.objects.filter(user=request.user))

        return JsonResponse({'success': True, 'cart_total': total})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    product_name = item.product.pro_name
    item.delete()
    messages.success(request, f"« {product_name} » a été retiré de votre panier.")
    return redirect('shop:view_cart')
    

@login_required
def confirm_order(request):
    if request.method == "POST":
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.error(request, "Votre panier est vide.")
            return redirect('shop:product_list_client')

        total = sum(item.total_price() for item in cart_items)

        order = Order.objects.create(user=request.user, total=total)

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.pro_price
            )

        cart_items.delete()
        messages.success(request, "Commande confirmée avec succès.")
        return redirect('shop:invoice', order_id=order.id)

    return redirect('shop:view_cart')


@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'client/cart/invoice.html', {'order': order})



from django.template.loader import render_to_string

@login_required
def download_invoice_html(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    html_content = render_to_string('client/cart/invoice.html', {'order': order})
    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="facture_{order_id}.html"'
    return response

@login_required
def download_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Chemin système pur pour xhtml2pdf
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'photos', 'logo.png')

    html_content = render_to_string('client/cart/invoice_pdf.html', {
        'order': order,
        'logo_path': logo_path,
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{order_id}.pdf"'
    
    # Création du PDF
    pisa_status = pisa.CreatePDF(html_content, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Une erreur est survenue lors de la création du PDF.')
    return response

@login_required
def client_dashboard(request):
    import json
    # Commandes de l'utilisateur
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Historique détaillé des articles achetés
    order_items = OrderItem.objects.filter(order__user=request.user).order_by('-order__created_at')
    
    # Nombre de produits achetés
    total_products_bought = sum(item.quantity for item in order_items)
    
    # Total dépensé
    total_spent = sum(order.total for order in orders)

    # Données pour le graphe
    labels = [order.created_at.strftime('%d/%m/%Y') for order in orders]
    data = [float(order.total) for order in orders]
    labels.reverse()
    data.reverse()

    context = {
        'orders': orders,
        'total_products_bought': total_products_bought,
        'total_spent': total_spent,
        'order_items': order_items[:10],
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data)
    }
    return render(request, 'client/dashboard.html', context)


# ============================================================
# ADMIN - Gestion des factures (vues par utilisateur)
# ============================================================
@user_passes_test(is_admin, login_url='shop:login')
def admin_invoices(request):
    search = request.GET.get('search', '')
    user_id = request.GET.get('user', '')

    orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')

    if search:
        orders = orders.filter(
            Q(user__firstname__icontains=search) |
            Q(user__lastname__icontains=search) |
            Q(user__email__icontains=search) |
            Q(id__icontains=search)
        )
    if user_id:
        orders = orders.filter(user_id=user_id)

    users = User.objects.all().order_by('firstname')

    return render(request, 'admin/invoices/list.html', {
        'orders': orders,
        'users': users,
        'selected_user': user_id,
        'search': search,
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_invoice_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'client/cart/invoice.html', {'order': order, 'is_admin_view': True})


# ============================================================
# ADMIN - Gestion des stocks
# ============================================================
@user_passes_test(is_admin, login_url='shop:login')
def admin_stock(request):
    from django.db.models import Sum

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    stock_filter = request.GET.get('stock_filter', '')

    products = Product.objects.select_related('category').all()

    if query:
        products = products.filter(
            Q(pro_name__icontains=query) |
            Q(category__cat_name__icontains=query)
        )
    if category_id:
        products = products.filter(category_id=category_id)
    if stock_filter == 'low':
        products = products.filter(stock__lte=5)
    elif stock_filter == 'out':
        products = products.filter(stock=0)

    # Mise à jour du stock via POST
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')
        if product_id and new_stock is not None:
            p = get_object_or_404(Product, pk=product_id)
            p.stock = int(new_stock)
            p.save()
            messages.success(request, f"Stock de '{ p.pro_name }' mis à jour : { p.stock } unités.")
            return redirect('shop:admin_stock')

    categories = Category.objects.all()
    total_stock = products.aggregate(total=Sum('stock'))['total'] or 0
    low_stock_count = Product.objects.filter(stock__lte=5, stock__gt=0).count()
    out_stock_count = Product.objects.filter(stock=0).count()

    return render(request, 'admin/stock/manage.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'stock_filter': stock_filter,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
        'out_stock_count': out_stock_count,
    })