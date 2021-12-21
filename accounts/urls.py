from django.urls import path
from . import views


app_name ='accounts'

urlpatterns =[
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('login-api/check-auth/', views.check_log_in_view, name='login-auth')
]