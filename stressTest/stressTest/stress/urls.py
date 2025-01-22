from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('check_connection_s', views.check_connection_status,
         name='check_connection_status'),
    path('check_progress', views.check_progress, name='check_progress'),
    path('get_file_detail', views.get_file_detail, name='get_file_detail'),
    path('do_test', views.do_test, name='do_test'),
]
