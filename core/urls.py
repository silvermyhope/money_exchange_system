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

    path('superadmin/dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/user/add/', views.create_user, name='create_user'),
    path('superadmin/user/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('superadmin/user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('superadmin/groups/add/', views.manage_groups, name='manage_groups'),

    path('transactions/receipt/<int:transaction_id>/', views.print_receipt, name='print_receipt'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)