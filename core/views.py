from django.shortcuts import render, redirect
from .models import Sender
from .forms import SenderForm
from .decorators import group_required

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
    query = request.GET.get('q')
    results = []
    if query:
        results = Sender.objects.filter(
            models.Q(full_name__icontains=query) |
            models.Q(phone__icontains=query) |
            models.Q(id_number__icontains=query)
        )
    return render(request, 'core/search_sender.html', {'results': results})
