from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

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
    path('search-receivers/', views.search_receivers, name='search_receivers'),

    path('ajax/register-receiver/', views.ajax_register_receiver, name='ajax_register_receiver'),
    path('ajax/register-sender/', views.ajax_register_sender, name='ajax_register_sender'),
     path('exchange-rates/', views.exchange_rates, name='exchange_rates'),
    path('exchange-rates/add/', views.add_exchange_rate, name='add_exchange_rate'),
    path('get-exchange-rate/', views.get_exchange_rate, name='get_exchange_rate'),

    path('transactions/update/<int:transaction_id>/', views.update_transaction, name='update_transaction'),
    path('transactions/detail/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('cashier/transactions/detail/<int:transaction_id>/', views.cashier_transaction_detail, name='cashier_transaction_detail'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)