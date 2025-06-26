from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.RoleBasedLoginView.as_view(), name='login'),
    path('cashier/dashboard/', views.cashier_dashboard, name='cashier_dashboard'),
    path('accountant/dashboard/', views.accountant_dashboard, name='accountant_dashboard'),
    path('send/', views.send_transaction, name='send_transaction'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    
    path('register-sender/', views.register_sender, name='register_sender'),
    path('search-sender/', views.search_sender, name='search_sender'),
    path('register-receiver/', views.register_receiver, name='register_receiver'),
    path('get-receivers/', views.get_receivers_by_sender, name='get_receivers_by_sender'),
]