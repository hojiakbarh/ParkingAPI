from decimal import Decimal
from http import HTTPStatus

from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView, DestroyAPIView, \
    RetrieveUpdateDestroyAPIView, get_object_or_404, RetrieveAPIView, ListCreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.models import User, ParkingZone, ParkingSpot, Reservation, Payment
from user.permissions import IsAdmin
from user.serializers import RegisterModelSerializer, ForgotSerializer, VerifyOTPSerializer, \
    ChangePasswordSerializer, ProfileModelSerializer, ParkingZoneModelSerializer, ParkingZoneDetailSerializer, \
    ParkingSpotSerializer, ReservationSerializer, PaymentSerializer


# Create your views here.


class RegisterCreateAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    permission_classes = [AllowAny]

@extend_schema(tags=['auth'])
class CustomTokenObtainPairView(TokenObtainPairView):
    pass

@extend_schema(tags=['auth'])
class CustomTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(tags=['auth'], request=ForgotSerializer)
class ForgotAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = ForgotSerializer(data=data)
        if serializer.is_valid():
            serializer.send_code(data['email'])
            return JsonResponse({'status': HTTPStatus.OK, 'message': "Tasdiqlash kodi yuborildi!"})
        return JsonResponse({"status": HTTPStatus.BAD_REQUEST, "message": "Bunday email topilmadi!"})


@extend_schema(tags=['auth'], request=VerifyOTPSerializer)
class VerifyOTPAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = VerifyOTPSerializer(data=data)
        if serializer.is_valid():
            return JsonResponse({'status': HTTPStatus.ACCEPTED, 'message': "Code tasdiqlandi!"})
        return JsonResponse({'status': HTTPStatus.BAD_REQUEST, "errors": "Bunday code topilmadi!"})


@extend_schema(tags=['auth'], request=ChangePasswordSerializer)
class ChangePasswordAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = ChangePasswordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'status': HTTPStatus.ACCEPTED, 'message': "Ma'lumotlar o'zgartirildi!"})
        return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message!': 'Xatolik!', 'errors': serializer.errors})



@extend_schema(tags=['profile'], request=ProfileModelSerializer)
@permission_classes([IsAuthenticated])
class ProfileAPIView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = ProfileModelSerializer(instance=user)
        return JsonResponse({'status': HTTPStatus.OK, 'message': serializer.data})


@extend_schema(tags=['profile'], request=ProfileModelSerializer)
@permission_classes([IsAuthenticated])
class ProfileUpdateAPIView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileModelSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user


@extend_schema(tags=['profile'], request=ProfileModelSerializer)
class ProfileListAPIView(ListAPIView):
    parser_classes = (MultiPartParser, FormParser)
    queryset = User.objects.all()
    serializer_class = ProfileModelSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=['profile'], request=ProfileModelSerializer)
class ProfileDeleteAPIView(DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileModelSerializer
    pk_url_kwarg = 'pk'
    permission_classes = [IsAuthenticated, IsAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return JsonResponse({'status': HTTPStatus.OK, 'message': "Muvaffaqiyatli o'chirildi!"})


# ======================== Parking zones========================

@extend_schema(tags=['parking-zone'])
class ParkingZoneListAPIView(CreateAPIView):
    queryset = ParkingZone.objects.all()
    serializer_class = ParkingZoneModelSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ParkingZoneDetailSerializer
        return ParkingZoneModelSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': HTTPStatus.OK, 'message': serializer.data})

    def create_parking_spots(self, zone):
        spots = []
        for i in range(1, zone.total_spots + 1):
            spot_type = 'regular'
            if i <= 2:
                spot_type = 'handicapped'
            elif i <= zone.total_spots * 0.1:
                spot_type = 'electric'

            spots.append(ParkingSpot(
                zone=zone,
                spot_type=spot_type,
                spot_number=f'A{i:03d}'
            ))
        ParkingSpot.objects.bulk_create(spots)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        zone = serializer.instance
        self.create_parking_spots(zone)
        return Response({'status': HTTPStatus.CREATED, 'message': "Parking Zone muvaffaqiyatli yaratildi!"})


@extend_schema(tags=['parking-zone'], request=ParkingZoneModelSerializer)
class ParkingZoneDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = ParkingZone.objects.all()
    serializer_class = ParkingZoneModelSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def available_spots(self, request, pk=None):
        zone = self.get_object()
        available_spots = zone.spots.filter(status='available', is_active=True)
        serializer = self.get_serializer(available_spots, many=True)
        return JsonResponse({'status': HTTPStatus.OK, 'message': serializer.data})





@extend_schema(tags=['parking-zone'], request=ParkingSpotSerializer)
class ParkingZoneSpotsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        zone = get_object_or_404(ParkingZone, pk=kwargs['pk'])
        available_spots = zone.spots.filter(status='available', is_active=True)
        serializer = ParkingSpotSerializer(available_spots, many=True)
        return JsonResponse({'status': HTTPStatus.OK, 'message': serializer.data})



#========================= Parking Spots ====================================

@extend_schema(tags=['spots'], request=ParkingSpotSerializer)
class SpotListAPIView(ListAPIView):
    serializer_class = ParkingSpotSerializer

    def get_queryset(self):
        return ParkingSpot.objects.all()

@extend_schema(tags=['spots'], request=ParkingSpotSerializer)
class SpotAvailableAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParkingSpotSerializer

    def get_queryset(self):
        return ParkingSpot.objects.filter(status='empty') # is_active=True


@extend_schema(tags=['spots'], request=ParkingSpotSerializer)
class SpotCreateAPIView(CreateAPIView):
    serializer_class = ParkingSpotSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            payment_method = serializer.validated_data.pop('payment_method')  # bu muhim!
            spot = serializer.save()

            reservation = Reservation.objects.create(
                user_id=self.request.user,
                spot_id=spot,
                status_total_amount=Reservation.StatusChoices.PENDING,
            )

            Payment.objects.create(
                reservation=reservation,
                user=self.request.user,
                payment_method=payment_method,
                status=Payment.StatusChoices.PENDING,
                transaction_id=reservation.id,
            )
        return Response({'status': HTTPStatus.CREATED, 'message': serializer.data})


@extend_schema(tags=['spots'], request=ParkingSpotSerializer)
class SpotUpdateAPIView(UpdateAPIView):
    queryset = ParkingSpot.objects.all()
    serializer_class = ParkingSpotSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


@extend_schema(tags=['spots'], request=ParkingSpotSerializer)
class SpotStatusAPIView(UpdateAPIView):
    queryset = ParkingSpot.objects.all()
    serializer_class = ParkingSpotSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        spot = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response({"detail": "Status is required."}, status=HTTPStatus.BAD_REQUEST)

        spot.status = new_status
        spot.save()

        serializer = self.get_serializer(spot)
        return Response(serializer.data, status=HTTPStatus.OK)


#=================== Reservations =================

@extend_schema(tags=['reservations'], request=ReservationSerializer)
class ReservationListCreateAPIView(ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reservations = Reservation.objects.filter(user_id=request.user)
        serializer = ReservationSerializer(reservations, many=True)
        return JsonResponse({'status': HTTPStatus.OK, 'data': serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = ReservationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user_id=request.user)
            return Response({'status': HTTPStatus.CREATED, 'message': serializer.data})
        return Response({'status': HTTPStatus.BAD_REQUEST, 'message': serializer.errors})



@extend_schema(tags=['reservations'], request=ReservationSerializer)
class ReservationDetailAPIView(APIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        data = request.data
        serializer = ReservationSerializer(data=data)
        return Response({'status': HTTPStatus.OK, 'message': serializer.data})

    def put(self, request, *args, **kwargs):
        data = request.data
        serializer = ReservationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': HTTPStatus.OK, 'message': serializer.data})
        return Response({'status': HTTPStatus.BAD_REQUEST, 'message': serializer.errors})

    def delete(self, request, pk, *args, **kwargs):
        reservation = get_object_or_404(Reservation, pk=pk)
        if reservation.user_id != self.request.user:
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': 'Topilmadi.'})
        reservation.delete()
        return Response({'status': HTTPStatus.OK, 'message': "Muvaffaqiyatli o'chirildi."})


@extend_schema(tags=['reservations'], request=ReservationSerializer)
class ReservationCheckInAPIView(APIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = ReservationSerializer(data=data)
        if serializer.is_valid():
            reservation = serializer.save(user_id=request.user)
            if reservation.status_total_amount != Reservation.StatusChoices.PENDING:
                return Response({'status': HTTPStatus.BAD_REQUEST, 'message': "Faqat 'pending' holatda check-in bo‘ladi!"})
            reservation.status_total_amount = Reservation.StatusChoices.ACTIVE
            reservation.save()
            return JsonResponse({'status': HTTPStatus.OK, 'message': "Check-in muvaffaqiyatli bajarildi!"})


@extend_schema(tags=['reservations'], request=ReservationSerializer)
class ReservationCheckOutAPIView(APIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, user_id=request.user)
        if reservation.status_total_amount != Reservation.StatusChoices.ACTIVE:
            return JsonResponse({'status': HTTPStatus.BAD_REQUEST, 'message': "Faqat 'active' holatda check-out bo‘ladi!"})
        reservation.status_total_amount = Reservation.StatusChoices.COMPLETED
        reservation.save()
        return JsonResponse({'status': HTTPStatus.OK, 'message': "Check-out muvaffaqiyatli bajarildi!"})


@extend_schema(tags=['payments'], request=PaymentSerializer)
class PaymentListCreateAPIView(ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        payments = Payment.objects.filter(user_id=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return JsonResponse({'status': HTTPStatus.OK, 'data': serializer.data}, safe=False)

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': HTTPStatus.CREATED, 'message': serializer.data})
        return Response({'status': HTTPStatus.BAD_REQUEST, 'message': serializer.errors})


class PaymentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, pk=pk, user_id=request.user)
        serializer = PaymentSerializer(payment)
        return Response({'status': HTTPStatus.OK, 'message': serializer.data})


class PaymentRefundAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = PaymentSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            refund = serializer.validated_data
            return Response({'message': 'Muvaffaqiyatli otkazildi!', 'status': HTTPStatus.OK})
        return Response({'status': HTTPStatus.BAD_REQUEST, 'message': serializer.errors})






# class ReservationListCreateAPIView(ListCreateAPIView):
#     queryset = Reservation.objects.all()
#     serializer_class = ReservationSerializer
#     permission_classes = [IsAuthenticated]
#
#     def perform_create(self, serializer):
#         serializer.save(user_id=self.request.user)
#
#
# class ReservationDetailAPIView(RetrieveUpdateDestroyAPIView):
#     queryset = Reservation.objects.all()
#     serializer_class = ReservationSerializer
#     permission_classes = [IsAuthenticated]
#
#
# class ReservationCheckInAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, pk):
#         reservation = get_object_or_404(Reservation, pk=pk, user_id=request.user)
#         if reservation.status_total_amount != Reservation.StatusChoices.PENDING:
#             return Response({"detail": "Cannot check in unless reservation is pending."}, status=status.HTTP_400_BAD_REQUEST)
#
#         reservation.status_total_amount = Reservation.StatusChoices.ACTIVE
#         reservation.save()
#         return Response({"detail": "Checked in successfully."}, status=status.HTTP_200_OK)
#
#
# class ReservationCheckOutAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, pk):
#         reservation = get_object_or_404(Reservation, pk=pk, user_id=request.user)
#         if reservation.status_total_amount != Reservation.StatusChoices.ACTIVE:
#             return Response({"detail": "Cannot check out unless reservation is active."}, status=status.HTTP_400_BAD_REQUEST)
#
#         reservation.status_total_amount = Reservation.StatusChoices.COMPLETED
#         reservation.save()
#         return Response({"detail": "Checked out successfully."}, status=status.HTTP_200_OK)












