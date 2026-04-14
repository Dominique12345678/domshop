from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST 
from .forms import CustomUserCreationForm, CategoryForm, ProductForm, CouponForm
from .models import User, Role, Product, Category, CartItem, Order, OrderItem, UserOTP, Wishlist, Review, Coupon
import json, random
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.http import HttpResponse
import tempfile
from xhtml2pdf import pisa
from django.conf import settings
import os
from django.utils import timezone



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
            if user.is_banned:
                messages.error(request, "Votre compte a été banni. Contactez le support.")
                return render(request, 'client/authentification/login.html')

            if not user.is_active:
                messages.error(request, "Veuillez confirmer votre email avant de vous connecter.")
                return redirect('shop:verify_otp', user_id=user.id)

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
            user = None
            try:
                user = form.save(commit=False)
                client_role, _ = Role.objects.get_or_create(role_name='client')
                user.role = client_role
                user.is_active = False  # Forcer confirmation par OTP
                user.save()

                # Génération et sauvegarde du code OTP
                otp_code = str(random.randint(100000, 999999))
                UserOTP.objects.update_or_create(
                    user=user,
                    defaults={'code': otp_code, 'created_at': timezone.now()}
                )

                # Envoi de l'email de confirmation (AMÉLIORÉ)
                subject = "Bienvenue sur DomShop - Code de confirmation"
                message = f"Bonjour {user.firstname},\n\nMerci d'avoir rejoint DomShop ! Pour activer votre compte, veuillez utiliser le code suivant :\n\n{otp_code}\n\nCe code expirera dans 10 minutes."
                from_email = settings.DEFAULT_FROM_EMAIL
                
                try:
                    send_mail(subject, message, from_email, [user.email])
                    messages.success(request, "Un code de confirmation a été envoyé à votre adresse email.")
                except Exception as mail_err:
                    print(f"Erreur email: {mail_err}")
                    messages.warning(request, "Compte créé, mais l'envoi de l'email a échoué. Contactez le support.")

                return redirect('shop:verify_otp', user_id=user.id)

            except Exception as e:
                # En cas d'erreur, supprimer l'utilisateur partiellement créé
                if user and user.pk:
                    user.delete()
                error_msg = str(e)
                # Fournir des messages d'erreur lisibles selon le type
                if 'UNIQUE constraint' in error_msg or 'unique' in error_msg.lower():
                    messages.error(request, "Un compte existe déjà avec cette adresse email.")
                elif 'mail' in error_msg.lower() or 'smtp' in error_msg.lower() or 'connection' in error_msg.lower():
                    messages.error(request, "Votre compte a été créé mais l'envoi de l'email a échoué. Veuillez contacter le support.")
                else:
                    messages.error(request, f"Une erreur est survenue lors de l'inscription : {error_msg}")
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
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'newest')

    from django.db.models import Avg, Q

    products = Product.objects.all().annotate(avg_rating=Avg('reviews__rating'))

    if query:
        products = products.filter(
            Q(pro_name__icontains=query) | 
            Q(pro_desc__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if min_price:
        products = products.filter(pro_price__gte=min_price)
    
    if max_price:
        products = products.filter(pro_price__lte=max_price)

    if sort_by == 'price_asc':
        products = products.order_by('pro_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-pro_price')
    elif sort_by == 'rating':
        products = products.order_by('-avg_rating')
    else:
        products = products.order_by('-created_at')

    categories = Category.objects.all()
    cart_items = CartItem.objects.filter(user=request.user).values_list('product_id', flat=True)
    wishlist_items = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    context = {
        'products': products,
        'categories': categories,
        'cart_items': cart_items,
        'wishlist_items': wishlist_items,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'query': query
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('client/products/product_grid.html', {**context, 'request': request})
        return JsonResponse({'html': html, 'count': products.count()})

    return render(request, 'client/products/list.html', context)


@login_required
def product_detail(request, product_id):
    """Vue détaillée d'un produit."""
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().order_by('-created_at')
    
    from django.db.models import Avg
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5
    
    in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': int(avg_rating),
        'in_wishlist': in_wishlist
    }
    return render(request, 'client/products/detail.html', context)


@login_required
def live_search(request):
    """Endpoint JSON pour la recherche live dans la navbar."""
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        from django.urls import reverse
        products = Product.objects.filter(
            Q(pro_name__icontains=q) | Q(pro_desc__icontains=q)
        ).annotate(avg_rating=Avg('reviews__rating'))[:6]
        for p in products:
            results.append({
                'name': p.pro_name,
                'price': str(p.pro_price),
                'image': p.photo.url if p.photo else None,
                'url': reverse('shop:product_detail', args=[p.id]),
            })
    return JsonResponse({'results': results})


@login_required
def cart_count(request):
    """Retourne le nombre d'articles dans le panier (pour init du badge)."""
    count = CartItem.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wish_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        wish_item.delete()
        action = 'removed'
        msg = f"« {product.pro_name} » retiré de votre liste de souhaits."
    else:
        action = 'added'
        msg = f"« {product.pro_name} » ajouté à votre liste de souhaits."
        
    return JsonResponse({'status': 'success', 'action': action, 'message': msg})

@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')
        
        Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment
        )
        messages.success(request, "Merci pour votre avis !")
        return redirect('shop:product_list_client')

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        code = data.get('code', '')
        
        from django.utils import timezone
        coupon = Coupon.objects.filter(
            code__iexact=code, 
            active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).first()
        
        if coupon:
            items = CartItem.objects.filter(user=request.user)
            subtotal = sum(item.total_price() for item in items)
            
            if coupon.discount_type == 'percent':
                discount = (subtotal * coupon.discount_percent) / 100
                label = f"{coupon.discount_percent}%"
            else:
                discount = coupon.discount_amount
                label = f"{coupon.discount_amount} FCFA"
                
            new_total = max(0, subtotal - discount)
            
            return JsonResponse({
                'success': True, 
                'discount_percent': coupon.discount_percent if coupon.discount_type == 'percent' else 0,
                'discount_amount': float(discount),
                'new_total': float(new_total),
                'message': f"Coupon '{code}' appliqué (-{label})"
            })
        else:
            return JsonResponse({'success': False, 'message': "Coupon invalide ou expiré."})



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
        cart_count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'status': status, 'message': msg, 'cart_count': cart_count})

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

        subtotal = sum(item.total_price() for item in cart_items)
        discount_amount = 0
        coupon_code = request.POST.get('coupon_applied', '').strip()

        if coupon_code:
            from django.utils import timezone
            from .models import Coupon
            coupon = Coupon.objects.filter(
                code__iexact=coupon_code,
                active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            ).first()
            if coupon:
                if coupon.discount_type == 'percent':
                    discount_amount = (subtotal * coupon.discount_percent) / 100
                else:
                    discount_amount = coupon.discount_amount
        
        final_total = subtotal - discount_amount

        order = Order.objects.create(
            user=request.user, 
            total=final_total,
            discount_amount=discount_amount,
            coupon_code=coupon_code,
            status='pending'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.pro_price
            )

        cart_items.delete()
        messages.success(request, f"Commande confirmée avec succès. {'(Réduction appliquée)' if discount_amount > 0 else ''}")
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
    if is_admin(request.user):
        order = get_object_or_404(Order, id=order_id)
    else:
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


# Vues pour les erreurs personnalisées
def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)


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

# Vues pour les erreurs personnalisées
def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

def error_403(request, exception):
    return render(request, '403.html', status=403)


def verify_otp(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        return redirect('shop:login')

    if request.method == 'POST':
        code = request.POST.get('code')
        otp = UserOTP.objects.filter(user=user, code=code).first()

        if otp and otp.is_valid():
            user.is_active = True
            user.save()
            otp.delete()
            messages.success(request, 'Votre compte est maintenant activé ! Connectez-vous.')
            return redirect('shop:login')
        else:
            messages.error(request, 'Code invalide ou expiré.')

    return render(request, 'client/authentification/verify_otp.html', {'user_obj': user})

def resend_otp(request, user_id):
    """Envoie à nouveau le code OTP."""
    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        return redirect('shop:login')
        
    otp_code = str(random.randint(100000, 999999))
    UserOTP.objects.update_or_create(
        user=user,
        defaults={'code': otp_code, 'created_at': timezone.now()}
    )
    
    subject = "Nouveau code de confirmation - DomShop"
    message = f"Bonjour {user.firstname},\n\nVoici votre nouveau code de validation : {otp_code}\n\nCe code est valable 10 minutes."
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        messages.success(request, "Un nouveau code a été envoyé !")
    except Exception as e:
        messages.error(request, "Échec de l'envoi de l'email. Vérifiez votre configuration.")
        
    return redirect('shop:verify_otp', user_id=user.id)

@user_passes_test(is_admin, login_url='shop:login')
def user_manage(request):
    query = request.GET.get('q', '')
    users = User.objects.all().order_by('-created_at')
    if query:
        users = users.filter(Q(email__icontains=query) | Q(firstname__icontains=query) | Q(lastname__icontains=query))
    return render(request, 'admin/users/manage.html', {'users': users, 'query': query})

@user_passes_test(is_admin, login_url='shop:login')
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_superuser:
        user.is_banned = True
        user.save()
        messages.success(request, f'Utilisateur {user.email} banni.')
    return redirect('shop:user_manage')

@user_passes_test(is_admin, login_url='shop:login')
def unban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_banned = False
    user.save()
    messages.success(request, f'Utilisateur {user.email} réactivé.')
    return redirect('shop:user_manage')

@user_passes_test(is_admin, login_url='shop:login')
def coupon_manage(request):
    """Gestion des codes promos par l'admin."""
    coupons = Coupon.objects.all().order_by('-valid_to')
    form = CouponForm()
    
    if request.method == 'POST':
        if 'delete_id' in request.POST:
            coupon = get_object_or_404(Coupon, id=request.POST['delete_id'])
            coupon.delete()
            messages.success(request, "Code promo supprimé.")
            return redirect('shop:coupon_manage')
            
        coupon_id = request.POST.get('coupon_id')
        if coupon_id:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            form = CouponForm(request.POST, instance=coupon)
        else:
            form = CouponForm(request.POST)
            
        if form.is_valid():
            form.save()
            messages.success(request, "Code promo enregistré !")
            return redirect('shop:coupon_manage')
            
    return render(request, 'admin/coupons/manage.html', {
        'coupons': coupons,
        'form': form,
    })

