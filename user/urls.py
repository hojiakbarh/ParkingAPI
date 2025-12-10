from drf_spectacular.views import SpectacularAPIView
from django.urls import path

from user.models import Reservation
from user.views import (RegisterCreateAPIView, ForgotAPIView, CustomTokenObtainPairView, CustomTokenRefreshView,
                        VerifyOTPAPIView, ChangePasswordAPIView, ProfileAPIView, ProfileUpdateAPIView,
                        ProfileListAPIView, ProfileDeleteAPIView, ParkingZoneListAPIView,
                        ParkingZoneDetailAPIView, ParkingZoneSpotsAPIView, SpotListAPIView, SpotAvailableAPIView,
                        SpotCreateAPIView, SpotUpdateAPIView, SpotStatusAPIView, ReservationListCreateAPIView,
                        ReservationDetailAPIView, ReservationCheckInAPIView, ReservationCheckOutAPIView,
                        PaymentListCreateAPIView, PaymentDetailAPIView, PaymentRefundAPIView)



# --------------------- AUTH ---------------
urlpatterns = [
    path('register', RegisterCreateAPIView.as_view(), name="register"),
    path('login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token-refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', ForgotAPIView.as_view(), name="forgot-password"),
    path('verify-otp', VerifyOTPAPIView.as_view(), name="verify_otp"),
    path('change-password', ChangePasswordAPIView.as_view(), name="change_password"),
]



# ----------------------- User / Profile ------------------------


urlpatterns += [
    path('profile/about', ProfileAPIView.as_view(), name="profile-about"),
    path('profile/update', ProfileUpdateAPIView.as_view(), name="profile-update"),
    path('profile/list', ProfileListAPIView.as_view(), name="profile-list"),
     path('profile/<int:pk>', ProfileDeleteAPIView.as_view(), name="profile-delete"),
]


# ------------------------ Parking zone ---------------------------

urlpatterns += [
    path('parking-zones', ParkingZoneListAPIView.as_view(), name="parking-zone-list"),
    path('parking-zones/detail/<int:pk>', ParkingZoneDetailAPIView.as_view(), name="parking-zone-update"),
    path('parking-zones-spots/<int:pk>/spots', ParkingZoneSpotsAPIView.as_view(), name="parking-zone-spots"),
]


# ====================== Parking Spots =========================

urlpatterns += [
    path('spots/list/', SpotListAPIView.as_view(), name="spots"),
    path('spots/available/', SpotAvailableAPIView.as_view(), name="spots-available"),
    path('spots/', SpotCreateAPIView.as_view(), name="spots-create"),
    path('spots/<int:pk>/', SpotUpdateAPIView.as_view(), name="spots-update"),
    path('spots/<int:pk>/status/', SpotStatusAPIView.as_view(), name='spots-status'),
]


#===================== Reservations =============================


urlpatterns += [
    path('reservations', ReservationListCreateAPIView.as_view(), name="reservation-list-create"),

    path('reservations/<int:pk>', ReservationDetailAPIView.as_view(), name="reservation-detail"),
    path('reservations/<int:pk>/checkin', ReservationCheckInAPIView.as_view(), name="reservation-checkin"),
    path('reservations/<int:pk>/checkout', ReservationCheckOutAPIView.as_view(), name="reservation-checkout"),
]


# =================== Payments ====================

urlpatterns += [
    path('payments', PaymentListCreateAPIView.as_view(), name="payment-list-create"),
    path('payments/<int:pk>', PaymentDetailAPIView.as_view(), name="payment-detail"),
    path('payments/<int:pk>/refund', PaymentRefundAPIView.as_view(), name="payment-refund"),
]


#===================













