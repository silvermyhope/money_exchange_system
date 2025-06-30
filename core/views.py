from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Sender, Receiver, ExchangeRate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .decorators import group_required
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum, Count, Q
from .forms import SenderForm, TransactionUpdateForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import random
import string
from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator


class RoleBasedLoginView(LoginView):
    template_name = 'registration/login.html'  # Or wherever your template is

    def get_success_url(self):
        user = self.request.user
        print("Login success for:", user.username)

        if user.groups.filter(name='Cashier').exists():
            print("Redirecting to cashier dashboard")
            return '/cashier/dashboard/'
        elif user.groups.filter(name='Accountant').exists():
            print("Redirecting to accountant dashboard")
            return '/accountant/dashboard/'
        print("Redirecting to fallback")
        return '/'



@login_required
@group_required('Cashier')
def cashier_dashboard(request):
    user = request.user
    today = now().date()

    transactions_list = Transaction.objects.filter(cashier=user).order_by('-created_at')
    paginator = Paginator(transactions_list, 10)  # 10 transactions per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    today_count = Transaction.objects.filter(cashier=user, created_at__date=today).count()

    context = {
        'today_count': today_count,
        'page_obj': page_obj
    }
    return render(request, 'core/cashier_dashboard.html', context)



@login_required
@group_required('Accountant')
def accountant_dashboard(request):
    today = now().date()
    total_transactions = Transaction.objects.count()
    totals_by_currency = Transaction.objects.values('currency').annotate(total_amount=Sum('amount'))

    transactions_list = Transaction.objects.all().order_by('-created_at')
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_transactions': total_transactions,
        'totals_by_currency': totals_by_currency,
        'page_obj': page_obj
    }
    return render(request, 'core/accountant_dashboard.html', context)



@login_required
@group_required('Cashier')
def send_transaction(request):
    today = now().date()
    rate_obj = ExchangeRate.objects.filter(date=today, to_currency='ETB').first()

    exchange_rate = rate_obj.rate if rate_obj else Decimal('1.0')
    service_fee_percent = Decimal('5.0')

    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        receiver_id = request.POST.get('receiver')
        amount = request.POST.get('amount')
        currency = request.POST.get('currency')
        exchanged_amount = request.POST.get('exchanged_amount')
        service_fee = request.POST.get('service_fee')

        try:
            amount_decimal = Decimal(amount)
            exchanged_decimal = Decimal(exchanged_amount)
            service_fee_decimal = Decimal(service_fee)
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, "Invalid amount entered.")
            return redirect('send_transaction')

        if sender_id and receiver_id:
            sender = Sender.objects.get(id=sender_id)
            receiver = Receiver.objects.get(id=receiver_id)
            pin = ''.join(random.choices(string.digits, k=6))

            Transaction.objects.create(
                sender=sender,
                receiver=receiver,
                amount=amount_decimal,
                currency=currency,
                exchanged_amount=exchanged_decimal,
                service_fee=service_fee_decimal,
                status='Pending',
                pin=pin,
                cashier=request.user
            )
            messages.success(request, f"Transaction created successfully! PIN: {pin}")
            return redirect('transaction_list')
        else:
            messages.error(request, "Both sender and receiver must be selected.")
            return redirect('send_transaction')

    return render(request, 'core/send_transaction.html', {
        'exchange_rate': float(exchange_rate),
        'service_fee_percent': float(service_fee_percent)
    })



@login_required
def transaction_list(request):
    if request.user.groups.filter(name='Cashier').exists():
        transactions = Transaction.objects.filter(cashier=request.user)
    elif request.user.groups.filter(name='Accountant').exists():
        transactions = Transaction.objects.all()
    else:
        return HttpResponseForbidden("You are not allowed to view transactions.")

    return render(request, 'core/transaction_list.html', {'transactions': transactions})


def home(request):
    return render(request, 'core/index.html')


# @login_required
# @group_required('Cashier')
# def search_or_register_sender(request):
#     query = request.GET.get('query', '')
#     sender_results = []
#     if query:
#         sender_results = Sender.objects.filter(
#             Q(full_name__icontains=query) |
#             Q(phone__icontains=query) |
#             Q(id_number__icontains=query)
#         )

#     if request.method == 'POST':
#         form = SenderForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Sender registered successfully.")
#             return redirect('search_or_register_sender')
#     else:
#         form = SenderForm()

#     return render(request, 'core/search_or_register_sender.html', {
#         'form': form,
#         'sender_results': sender_results,
#         'query': query
#     })







@login_required
@group_required('Cashier')
def register_sender(request):
    form = SenderForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('register_sender')
    return render(request, 'core/register_sender.html', {'form': form})

@group_required('Cashier')
def search_sender(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        senders = Sender.objects.filter(
            Q(full_name__icontains=query) | Q(phone__icontains=query)
        ).values('id', 'full_name', 'phone', 'id_number')[:5]

        results = list(senders)

    return JsonResponse(results, safe=False)


def generate_unique_pin():
    from .models import Transaction
    while True:
        pin = ''.join(random.choices(string.digits, k=6))
        if not Transaction.objects.filter(pin=pin).exists():
            return pin
        

@login_required
@group_required('Cashier')
def register_receiver(request):
    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        name = request.POST.get('name')
        country = request.POST.get('country')
        phone = request.POST.get('phone')
        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')

        sender = Sender.objects.get(id=sender_id)

        Receiver.objects.create(
            sender=sender,
            name=name,
            country=country,
            phone=phone,
            bank_name=bank_name,
            account_number=account_number
        )
        messages.success(request, "Receiver registered successfully!")
        return redirect('send_transaction')
    
    # This part renders the form with all senders in a dropdown
    senders = Sender.objects.all()
    return render(request, 'core/register_receiver.html', {'senders': senders})



@login_required
@group_required('Cashier')
def search_receivers(request):
    sender_id = request.GET.get('sender_id')
    receivers = []

    if sender_id:
        receivers_qs = Receiver.objects.filter(sender_id=sender_id).values('id', 'name', 'phone', 'country', 'bank_name', 'account_number')
        receivers = list(receivers_qs)

    return JsonResponse(receivers, safe=False)


@csrf_exempt
@require_POST
@login_required
@group_required('Cashier')
def ajax_register_receiver(request):
    sender_id = request.POST.get('sender_id')
    name = request.POST.get('name')
    country = request.POST.get('country')
    phone = request.POST.get('phone')
    bank_name = request.POST.get('bank_name')
    account_number = request.POST.get('account_number')

    try:
        sender = Sender.objects.get(id=sender_id)
        receiver = Receiver.objects.create(
            sender=sender,
            name=name,
            country=country,
            phone=phone,
            bank_name=bank_name,
            account_number=account_number
        )
        return JsonResponse({'status': 'success', 'receiver': {
            'id': receiver.id,
            'name': receiver.name,
            'phone': receiver.phone,
            'country': receiver.country,
            'bank_name': receiver.bank_name,
            'account_number': receiver.account_number,
        }})
    except Sender.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sender not found'}, status=404)
    

@csrf_exempt
@require_POST
@login_required
@group_required('Cashier')
def ajax_register_sender(request):
    if request.method == 'POST':
        sender = Sender.objects.create(
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            dob=request.POST['dob'],
            id_number=request.POST['id_number'],
            id_issued_date=request.POST['id_issued_date'],
            id_expiry_date=request.POST['id_expiry_date'],
        )
        return JsonResponse({
            'status': 'success',
            'sender': {
                'id': sender.id,
                'full_name': sender.full_name,
                'phone': sender.phone,
                'id_number': sender.id_number
            }
        })


@login_required
@group_required('Cashier')
def exchange_rates(request):
    rates = ExchangeRate.objects.all()
    return render(request, 'core/exchange_rates.html', {'rates': rates})


@login_required
@group_required('Cashier')
def add_exchange_rate(request):
    if request.method == 'POST':
        from_currency = request.POST.get('from_currency')
        to_currency = request.POST.get('to_currency')
        rate = request.POST.get('rate')
        date = request.POST.get('date') or timezone.now().date()

        if from_currency and to_currency and rate:
            ExchangeRate.objects.create(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                date=date
            )
        return redirect('exchange_rates')


@login_required
@group_required('Cashier')
def get_exchange_rate(request):
    currency = request.GET.get('currency')
    today = now().date()

    rate_obj = ExchangeRate.objects.filter(date=today, from_currency=currency, to_currency='ETB').first()

    if rate_obj:
        return JsonResponse({'rate': float(rate_obj.rate)})
    else:
        return JsonResponse({'rate': 160})
    

@login_required
@group_required('Accountant')
def update_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.method == 'POST':
        form = TransactionUpdateForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            updated_transaction = form.save(commit=False)
            updated_transaction.updated_by = request.user
            updated_transaction.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)

    else:
        form = TransactionUpdateForm(instance=transaction)
        return render(request, 'core/partial_update_transaction.html', {'form': form, 'transaction': transaction})
    

@login_required
@group_required('Accountant')
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'core/partial_transaction_detail.html', {'transaction': transaction})

@login_required
@group_required('Cashier')
def cashier_transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'core/partial_transaction_detail.html', {'transaction': transaction})