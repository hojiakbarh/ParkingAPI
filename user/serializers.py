import re
import random
from redis import Redis
from datetime import timedelta
from user.models import User, ParkingZone, ParkingSpot, Payment, Reservation
from rest_framework.utils import json
from django.core.mail import send_mail
from root.settings import EMAIL_HOST_USER
from rest_framework.fields import CharField
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
import datetime

class RegisterModelSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'phone', 'first_name', 'last_name')
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_password(self, value):
        return make_password(value)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError('Username already exists')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError('Email already exists')
        return value

    def validate_phone(self, value):
        # Remove all non-digits
        cleaned = re.sub(r'\D', '', value)

        # Check if phone exists
        if User.objects.filter(phone=cleaned).exists():
            raise ValidationError('Phone already exists')

        # Only numbers allowed
        if value != cleaned:
            raise ValidationError('Phone number must contain only digits')

        # Return cleaned version
        return cleaned


class ForgotSerializer(Serializer):
    email = CharField(max_length=255)

    def validate_email(self, value):
        query = User.objects.filter(email=value)
        if not query.exists():
            raise ValidationError("Bunday email topilmadi.")
        return value

    def send_code(self, email):
        code = random.randint(10**5, 10**6)
        redis = Redis(decode_responses=True)
        data = {"code": code, "status": "False"}
        data_str = json.dumps(data)
        redis.mset({email: data_str })
        redis.expire(email, time=timedelta(minutes=1))
        send_mail(
            subject='Verification Code!!!',
            message=f"{code}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )


class VerifyOTPSerializer(Serializer):
    email = CharField(max_length=255)
    code = CharField(max_length=10)

    def validate(self, attrs):
        redis = Redis()
        email = attrs.get('email')
        code = attrs.get('code')

        data_list = redis.mget(email)[0]
        if not data_list or not data_list[0]:
            raise ValidationError("Code expired!")

        data_dict = json.loads(data_list)  # <-- bu yer to'g'rilandi

        verify_code = str(data_dict.get('code'))
        if str(verify_code) != str(code):
            raise ValidationError("Code xato!")

        redis.set(email, json.dumps({'status': "True"}))
        redis.expire(email, timedelta(minutes=2))

        return attrs
    # def validate(self, attrs):
    #     redis = Redis()
    #     email = attrs.get('email')
    #     code = attrs.get('code')
    #     data_str = redis.mget(email) # {"code": ... , "status": .....}
    #     if not data_str:
    #         raise ValidationError("Code expired!")
    #     data_dict:dict = json.loads(data_str)
    #     verify_code = data_dict.get('code')
    #     if verify_code != code:
    #         raise ValidationError("Code xato!")
    #     redis.mset({email: json.dumps({'status': True})})
    #     redis.expire(email, time=timedelta(minutes=2))
    #     return attrs


class ChangePasswordSerializer(Serializer):
    email = CharField(max_length=255)
    password = CharField(max_length=255)
    confirm_password = CharField(max_length=255)
    def validate_email(self, value):
        redis = Redis()
        data_str = redis.mget(value)[0]
        if data_str == None or len(data_str) == 0:
            raise ValidationError("Code vaqti tugadi!")
        data_dict = json.loads(data_str)
        status = data_dict.get('status')
        if status == "False":
            raise ValidationError("Oldin email tasdiqlansin!")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Password Confirm passwordga teng emas!")
        attrs['password'] = make_password(password)
        return attrs

    def save(self, **kwargs):
        data = self.validated_data
        email = data.get('email')
        password = data.get('password')
        User.objects.filter(email=email).update(password=password)



class ProfileModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role')
        read_only_fields = ('email', 'role')

    def validate_phone(self, value):
        return re.sub(r'\D', '', value)




class ParkingZoneModelSerializer(ModelSerializer):
    created_at = serializers.DateTimeField(required=True)

    class Meta:
        model = ParkingZone
        fields = ('id', 'name', 'created_at', 'total_spots', 'available_spots', 'address', 'coordinates')
        read_only_fields = ('created_at', 'id')

    def validate_created_at(self, value):
        if isinstance(value, str):
            dt = parse_datetime(value)
            if dt is None:
                raise serializers.ValidationError("created_at must be a valid datetime string.")
            return dt
        elif isinstance(value, datetime.datetime):
            return value
        else:
            raise serializers.ValidationError("created_at must be a datetime or ISO datetime string.")

    def validate_updated_at(self, value):
        if isinstance(value, str):
            dt = parse_datetime(value)
            if dt is None:
                raise serializers.ValidationError("updated_at must be a valid datetime string.")
            return dt
        elif isinstance(value, datetime.datetime):
            return value
        else:
            raise serializers.ValidationError("updated_at must be a datetime or ISO datetime string.")



class ParkingZoneDetailSerializer(serializers.ModelSerializer):
    # hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    # daily_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    # monthly_rate = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = ParkingZone
        fields = (
            'id', 'name', 'address', 'coordinates', 'total_spots', 'available_spots', 'created_at'
        )


class ParkingSpotSerializer(ModelSerializer):
    payment_method = serializers.ChoiceField(
        choices=Payment.PaymentMethodChoices.choices,
        write_only=True
    )

    class Meta:
        model = ParkingSpot
        fields = ['id', 'zone', 'spot_number', 'spot_type', 'status', 'payment_method']
        read_only_fields = ['id', 'status']




class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'reservation_id', 'user_id', 'payment_method', 'status', 'transaction_id', 'created_at']
        # read_only_fields = ['status', 'transaction_id', 'created_at']

    def create(self, validated_data):
        validated_data.pop('payment_method', None)
        payment_method = Payment.objects.create(**validated_data)
        return payment_method
        # validated_data.pop('status', None)
        # validated_data.pop('transaction_id', None)


class ReservationSerializer(ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'user_id', 'spot_id', 'start_time', 'end_time', 'status_total_amount']
        read_only_fields = ('id', 'user_id')


