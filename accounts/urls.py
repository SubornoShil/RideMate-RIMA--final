from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("verify/", views.verify_phone, name="verify_phone"),
    path("verify/resend/", views.resend_otp, name="resend_otp"),
    path("verify-email/resend/", views.resend_email, name="resend_email"),
    path("verify-email/<str:token>/", views.verify_email, name="verify_email"),
]
