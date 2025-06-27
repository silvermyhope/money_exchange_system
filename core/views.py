from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Sender, Receiver
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .decorators import group_required
from django.utils.timezone import now
from django.db.models import Sum, Count, Q
from .forms import SenderForm
import random
import string


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

    recent_transactions = Transaction.objects.filter(cashier=user).order_by('-created_at')[:10]
    today_count = Transaction.objects.filter(cashier=user, created_at__date=today).count()

    context = {
        'recent_transactions': recent_transactions,
        'today_count': today_count,
    }
    return render(request, 'core/cashier_dashboard.html', context)



@login_required
@group_required('Accountant')
def accountant_dashboard(request):
    today = now().date()
    total_transactions = Transaction.objects.count()

    totals_by_currency = Transaction.objects.values('currency').annotate(total_amount=Sum('amount'))

    recent_transactions = Transaction.objects.all().order_by('-created_at')[:10]

    context = {
        'total_transactions': total_transactions,
        'totals_by_currency': totals_by_currency,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'core/accountant_dashboard.html', context)

@login_required
@group_required('Cashier')
def send_transaction(request):
    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        receiver_id = request.POST.get('receiver')
        amount = request.POST.get('amount')
        currency = request.POST.get('currency')

        if not sender_id or not receiver_id:
            messages.error(request, "Both sender and receiver must be selected.")
            return redirect('send_transaction')

        try:
            sender = Sender.objects.get(id=sender_id)
            receiver = Receiver.objects.get(id=receiver_id)
        except (Sender.DoesNotExist, Receiver.DoesNotExist):
            messages.error(request, "Invalid sender or receiver.")
            return redirect('send_transaction')

        pin = generate_unique_pin()

        transaction = Transaction.objects.create(
            sender=sender,
            receiver=receiver,
            amount=amount,
            currency=currency,
            status='Pending',
            pin=pin,
            cashier=request.user,
        )
        messages.success(request, f"Transaction created! PIN: {transaction.pin}")
        return redirect('transaction_list')

    return render(request, 'core/send_transaction.html')




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


@login_required
@group_required('Cashier')
def search_or_register_sender(request):
    query = request.GET.get('query', '')
    sender_results = []
    if query:
        sender_results = Sender.objects.filter(
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(id_number__icontains=query)
        )

    if request.method == 'POST':
        form = SenderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sender registered successfully.")
            return redirect('search_or_register_sender')
    else:
        form = SenderForm()

    return render(request, 'core/search_or_register_sender.html', {
        'form': form,
        'sender_results': sender_results,
        'query': query
    })







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
        receivers_qs = Receiver.objects.filter(sender_id=sender_id).values('id', 'name', 'phone')
        receivers = list(receivers_qs)

    return JsonResponse(receivers, safe=False)