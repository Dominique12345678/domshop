from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import validate_email
from django.conf import settings
from django.utils import timezone



class Role(models.Model):
    role_name = models.CharField(max_length=45, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.role_name

    class Meta:
        db_table = 'roles'


class UserManager(BaseUserManager):
    def create_user(self, email, firstname, lastname, password=None, **extra_fields):
        if not email:
            raise ValueError('Les utilisateurs doivent avoir une adresse email')
        
        email = self.normalize_email(email)
        role = extra_fields.pop('role', None) or Role.objects.get_or_create(role_name='client')[0]
        
        user = self.model(
            email=email,
            firstname=firstname,
            lastname=lastname,
            role=role,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, firstname, lastname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = Role.objects.get_or_create(role_name='admin')[0]
        
        return self.create_user(
            email=email,
            firstname=firstname,
            lastname=lastname,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    firstname = models.CharField(max_length=45)
    lastname = models.CharField(max_length=45)
    email = models.EmailField(max_length=45, unique=True, validators=[validate_email])
    password = models.CharField(max_length=128)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=False) # Inactif par défaut pour confirmation email
    is_staff = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstname', 'lastname']

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        db_table = 'users'


class Category(models.Model):
    cat_name = models.CharField(max_length=45)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.cat_name

    class Meta:
        db_table = 'categories'

class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        # Valide pendant 10 minutes
        return (timezone.now() - self.created_at).total_seconds() < 600



class Product(models.Model):
    pro_name = models.CharField(max_length=45)
    pro_price = models.DecimalField(max_digits=10, decimal_places=2)
    pro_desc = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    photo = models.ImageField(upload_to='product_photos/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0, verbose_name='Stock disponible')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pro_name

    class Meta:
        db_table = 'products'

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_gallery/')
    is_main = models.BooleanField(default=False)

    class Meta:
        db_table = 'product_images'

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)  # 1 to 5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = 'wishlist'
        unique_together = ('user', 'product')

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percent', 'Pourcentage'),
        ('amount', 'Montant fixe'),
    )
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent')
    discount_percent = models.PositiveIntegerField(null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    class Meta:
        db_table = 'coupons'



class Sale(models.Model):
    sale_code = models.CharField(max_length=45, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sale_code

    class Meta:
        db_table = 'sales'


class Bill(models.Model):
    qty = models.IntegerField()
    bill_code = models.CharField(max_length=45, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.bill_code

    class Meta:
        db_table = 'bills'


class PayMethod(models.Model):
    pay_name = models.CharField(max_length=45, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pay_name

    class Meta:
        db_table = 'paymethods'


class Payment(models.Model):
    paymethod = models.ForeignKey(PayMethod, on_delete=models.PROTECT)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Paiement via {self.paymethod} pour {self.sale}"

    class Meta:
        db_table = 'payments'

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)  # Référence par chaîne
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.product.pro_price

    def __str__(self):
        return f"{self.product.pro_name} x {self.quantity} pour {self.user.username}"



class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('prepared', 'En préparation'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande #{self.id}"

    class Meta:
        db_table = 'orders'



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.pro_name} pour commande #{self.order.id}"

    class Meta:
        db_table = 'order_items'
