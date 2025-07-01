from django import forms
from .models import Sender, Receiver, Transaction
from django.contrib.auth.models import User, Group


class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        fields = ['full_name', 'phone', 'address', 'dob', 'id_number', 'id_issued_date', 'id_expiry_date']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'id_issued_date': forms.DateInput(attrs={'type': 'date'}),
            'id_expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if Sender.objects.filter(id_number=id_number).exists():
            raise forms.ValidationError("A sender with this ID number already exists.")
        return id_number
    
class ReceiverForm(forms.ModelForm):
    class Meta:
        model = Receiver
        fields = ['sender', 'name', 'country', 'phone', 'bank_name', 'account_number']

class TransactionUpdateForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['status', 'receipt']
        widgets = {
            'status': forms.Select(choices=[
                ('Pending', 'Pending'),
                ('Sent', 'Sent'),
                ('Processing', 'Processing'),
                ('Completed', 'Completed'),
                ('Cancelled', 'Cancelled')
            ])
        }


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'groups']