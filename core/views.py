from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Sender, Receiver, ExchangeRate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .decorators import group_required
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum, Count, Q
from .forms import SenderForm, TransactionUpdateForm, UserForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import random
import string
from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
from django.template.loader import render_to_string



def home(request):
    return render(request, 'core/index.html')

@login_required
@group_required('SuperAdmin')
def superadmin_dashboard(request):
    users = User.objects.all().order_by('-date_joined')
    form = UserForm()
    return render(request, 'core/superadmin_dashboard.html', {'users': users, 'form': form})

@login_required
@group_required('SuperAdmin')
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            form.save_m2m()
            messages.success(request, 'User created successfully.')
        else:
            messages.error(request, 'Failed to create user.')
    return redirect('superadmin_dashboard')

@login_required
@group_required('SuperAdmin')
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            form.save_m2m()
            messages.success(request, 'User updated successfully.')
            return redirect('superadmin_dashboard')
        else:
            messages.error(request, 'Failed to update user.')
    else:
        form = UserForm(instance=user)
    return render(request, 'core/partial_user_form.html', {'form': form, 'user': user})


@login_required
@group_required('SuperAdmin')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully.')
    return redirect('superadmin_dashboard')

@login_required
@group_required('SuperAdmin')
def manage_groups(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        if group_name:
            Group.objects.get_or_create(name=group_name)
            messages.success(request, f'Role "{group_name}" created successfully.')
        else:
            messages.error(request, "Role name cannot be empty.")
        return redirect('superadmin_dashboard')

class RoleBasedLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user
        print("Login success for:", user.username)

        if user.groups.filter(name='SuperAdmin').exists():
            print("Redirecting to superadmin dashboard")
            return '/superadmin/dashboard/'
        elif user.groups.filter(name='Agent').exists():
            print("Redirecting to Agent dashboard")
            return '/agent/dashboard/'
        elif user.groups.filter(name='Accountant').exists():
            print("Redirecting to accountant dashboard")
            return '/accountant/dashboard/'
        print("Redirecting to fallback")
        return '/'



@login_required
@group_required('Agent')
def agent_dashboard(request):
    user = request.user
    today = now().date()

    transactions_list = Transaction.objects.filter(agent=user).order_by('-created_at')
    paginator = Paginator(transactions_list, 10)  # 10 transactions per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    today_count = Transaction.objects.filter(agent=user, created_at__date=today).count()

    context = {
        'today_count': today_count,
        'page_obj': page_obj
    }
    return render(request, 'core/agent_dashboard.html', context)



@login_required
@group_required('Accountant')
def accountant_dashboard(request):
    today = now().date()
    total_transactions = Transaction.objects.count()
    totals_by_currency = Transaction.objects.values('from_currency').annotate(total_amount=Sum('sending_amount'))

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
@group_required('Agent')
def send_transaction(request):
    today = now().date()
    rate_obj = ExchangeRate.objects.filter(date=today, to_currency='ETB').first()

    exchange_rate = rate_obj.rate if rate_obj else Decimal('1.0')
    service_charge_percent = Decimal('5.0')

    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        receiver_id = request.POST.get('receiver')
        sending_amount = request.POST.get('sending_amount')
        from_currency = request.POST.get('from_currency')
        exchanged_amount = request.POST.get('exchanged_amount')
        service_charge = request.POST.get('service_charge')

        try:
            amount_decimal = Decimal(sending_amount)
            exchanged_decimal = Decimal(exchanged_amount)
            service_charge_decimal = Decimal(service_charge)
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
                sending_amount=amount_decimal,
                from_currency=from_currency,
                exchanged_amount=exchanged_decimal,
                service_charge=service_charge_decimal,
                status='Pending',
                pin=pin,
                agent=request.user
            )
            messages.success(request, f"Transaction created successfully! PIN: {pin}")
            return redirect('transaction_list')
        else:
            messages.error(request, "Both sender and receiver must be selected.")
            return redirect('send_transaction')

    return render(request, 'core/send_transaction.html', {
        'exchange_rate': float(exchange_rate),
        'service_charge_percent': float(service_charge_percent)
    })



@login_required
def transaction_list(request):
    if request.user.groups.filter(name='agent').exists():
        transactions = Transaction.objects.filter(agent=request.user).order_by('-created_at')
    elif request.user.groups.filter(name='Accountant').exists():
        transactions = Transaction.objects.all().order_by('-created_at')
    else:
        return HttpResponseForbidden("You are not allowed to view transactions.")

    paginator = Paginator(transactions, 10)  # 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/transaction_list.html', {'page_obj': page_obj})


@login_required
@group_required('Agent')
def register_sender(request):
    form = SenderForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('register_sender')
    return render(request, 'core/register_sender.html', {'form': form})

@group_required('Agent')
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
@group_required('Agent')
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
@group_required('Agent')
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
@group_required('Agent')
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
@group_required('Agent')
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
@group_required('SuperAdmin')
def exchange_rates(request):
    rates = ExchangeRate.objects.all()
    return render(request, 'core/exchange_rates.html', {'rates': rates})


@login_required
@group_required('SuperAdmin')
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
@group_required('Agent')
def get_exchange_rate(request):
    from_currency = request.GET.get('from_currency')
    today = now().date()

    rate_obj = ExchangeRate.objects.filter(date=today, from_currency=from_currency, to_currency='ETB').first()

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
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # Restrict access: Cashiers can only view their own transactions
    if request.user.groups.filter(name='Agent').exists():
        if transaction.agent != request.user:
            return HttpResponseForbidden('Access denied.')

    return render(request, 'core/partial_transaction_detail.html', {'transaction': transaction})


@login_required
@group_required('Agent')
def print_receipt(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    sender = transaction.sender
    receiver = transaction.receiver

    return render(request, 'core/receipt.html', {
        'transaction': transaction,
        'sender': sender,
        'receiver': receiver,
    })


@login_required
@group_required('Agent')
def get_receipt_modal(request, transaction_id):
    print("Receipt view hit for transaction:", transaction_id)  # DEBUG

    try:
        transaction = get_object_or_404(Transaction, pk=transaction_id)
        sender = transaction.sender
        receiver = transaction.receiver

        html = render_to_string('core/receipt_modal_content.html', {
            'transaction': transaction,
            'sender': sender,
            'receiver': receiver,
        }, request=request)

        return JsonResponse({'html': html})

    except Exception as e:
        print("ERROR in get_receipt_modal:", e)  # DEBUG
        return JsonResponse({'error': str(e)}, status=500)
