from django.urls import path

from . import views

app_name = "rides"

urlpatterns = [
    path("", views.home, name="home"),
    path("rides/new/", views.ride_new, name="ride_new"),
    path("rides/<int:pk>/", views.ride_detail, name="ride_detail"),
    path("rides/<int:pk>/request/", views.ride_request, name="ride_request"),
    path("rides/<int:pk>/complete/", views.ride_complete, name="ride_complete"),
    path("rides/<int:pk>/cancel/", views.ride_cancel, name="ride_cancel"),
    path("requests/<int:pk>/accept/", views.request_accept, name="request_accept"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
    path("requests/<int:pk>/cancel/", views.request_cancel, name="request_cancel"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
