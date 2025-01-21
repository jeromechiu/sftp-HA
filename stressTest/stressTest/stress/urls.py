from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('check_connection_status/', views.check_connection_status,
         name='check_connection_status/'),
    path('do_test', views.do_test, name='do_test'),
]
