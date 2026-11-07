from django.urls import path

from . import views

app_name = "trust"

urlpatterns = [
    path("rides/<int:pk>/review/<int:profile_id>/", views.review_new, name="review_new"),
    path("profile/", views.profile, name="profile"),
    path("profile/guardians/add/", views.guardian_add, name="guardian_add"),
    path("profile/guardians/<int:pk>/delete/", views.guardian_delete, name="guardian_delete"),
    path("circles/", views.circles, name="circles"),
    path("circles/join/", views.circle_join, name="circle_join"),
    path("circles/<int:pk>/leave/", views.circle_leave, name="circle_leave"),
    path("notifications/", views.notifications, name="notifications"),
    path("analytics/", views.analytics, name="analytics"),
]
