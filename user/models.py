from django.contrib.auth.hashers import make_password
from django.db.models import DateTimeField
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models import TextChoices, Model, ForeignKey, CASCADE
from django.db.models.fields import CharField, PositiveIntegerField, TextField
from rest_framework.fields import DecimalField, BooleanField


# Create your models here.


class CustomerUser(UserManager):
    def _create_user_object(self,email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        return user

    def create_user(self,email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user( email, password, **extra_fields)

    def create_superuser(self,email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def _create_user(self, email, password, **extra_fields):
        user = self._create_user_object(email, password, **extra_fields)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    class RoleType(TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'
        SUPER_ADMIN = 'super admin', 'Super Admin'
    phone = CharField(max_length=100, unique=True)
    role = CharField(choices=RoleType, default=RoleType.USER, max_length=100)
    objects = CustomerUser()


class ParkingZone(Model):
    name = CharField(max_length=255, unique=True)
    address = TextField()
    coordinates = CharField(max_length=255)
    total_spots = PositiveIntegerField()
    available_spots = PositiveIntegerField()
    hourly_rate = DecimalField(max_digits=10, decimal_places=2)
    daily_rate = DecimalField(max_digits=10, decimal_places=2)
    monthly_rate = DecimalField(max_digits=10, decimal_places=2)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.coordinates} - {self.created_at}"


class ParkingSpot(Model):
    class StatusChoices(TextChoices):
        EMPTY = 'empty', 'Bo‘sh'
        OCCUPIED = 'occupied', 'Band'
        RESERVED = 'reserved', 'Zaxiralangan'
        MAINTENANCE = 'maintenance', 'Texnik xizmat'

    class SpotType(TextChoices):
        REGULAR = 'regular', 'Muntazam'
        HANDICAPPED = 'handicapped', 'Nogiron'
        ELECTRIC = 'electric', 'Electric'
        VIP = 'vip', 'VIP'

    zone = ForeignKey('user.ParkingZone', on_delete=CASCADE, related_name='parking_spots')
    spot_number = CharField(max_length=20)
    status = CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.EMPTY)
    spot_type = CharField(max_length=20, choices=SpotType.choices, default=SpotType.REGULAR)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('zone', 'spot_number')

    def __str__(self):
        return f"{self.zone.name} - {self.spot_number} - {self.created_at.strftime('%d/%m/%Y %H:%M')} - {self.is_active}"


class Reservation(Model):
    class StatusChoices(TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        ACTIVE = 'active', 'Faol'
        COMPLETED = 'completed', 'Yakunlandi'
        CANCELLED = 'cancelled', 'Bekor qilindi'

    user_id = ForeignKey('user.User', CASCADE, related_name='reservations')
    spot_id = ForeignKey('user.ParkingSpot', CASCADE, related_name='reservations')
    start_time = DateTimeField(auto_now_add=True)
    end_time = DateTimeField(auto_now=True)
    status_total_amount = CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    def __str__(self):
        return f"{self.user_id} - {self.spot_id} - {self.start_time} - {self.end_time}"


class Payment(Model):
    class PaymentMethodChoices(TextChoices):
        CLICK = 'click', 'Click'
        PAYME = 'payme', 'Payme'
        CARD = 'card', 'Card'
        CASH = 'cash', 'Naqd'

    class StatusChoices(TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        SUCCESS = 'success', "To'landi"
        FAILED = 'failed', "Muvaffaqiyatsiz"


    reservation = ForeignKey('user.Reservation', CASCADE, related_name='payments')
    user = ForeignKey('user.User', CASCADE, related_name='user_payments')
    price = DecimalField(max_digits=10, decimal_places=2)
    payment_method = CharField(choices=PaymentMethodChoices.choices, max_length=20, default=PaymentMethodChoices.CLICK)
    status = CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    # transaction_id = ForeignKey('user.Payment', on_delete=CASCADE, related_name='payments')
    transaction_id = CharField(max_length=20, unique=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} - {self.payment_method} - {self.status} - {self.transaction_id} - {self.reservation_id}"







