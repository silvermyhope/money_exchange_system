from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Transaction, Sender
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .decorators import group_required
from django.utils.timezone import now
from django.db.models import Sum, Count
from .forms import SenderForm


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
    recent_transactions = Transaction.objects.filter(sender=user).order_by('-created_at')[:10]
    today_count = Transaction.objects.filter(sender=user, created_at__date=today).count()

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

        sender = Sender.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        Transaction.objects.create(
            sender=sender,
            receiver=receiver,
            amount=amount,
            currency=currency,
            status='Pending'
        )
        return redirect('transaction_list')

    users = User.objects.exclude(id=request.user.id)
    return render(request, 'core/send_transaction.html', {'users': users})



@login_required
def transaction_list(request):
    if request.user.groups.filter(name='Cashier').exists():
        transactions = Transaction.objects.filter(sender=request.user)
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
    senders = Sender.objects.filter(
        Q(full_name__icontains=query) |
        Q(phone__icontains=query) |
        Q(id_number__icontains=query)
    )
    results = [{'id': s.id, 'full_name': s.name, 'phone': s.phone} for s in senders]
    return JsonResponse(results, safe=False)
