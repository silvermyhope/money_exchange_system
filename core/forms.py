from django import forms
from .models import Sender

class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        fields = ['full_name', 'phone', 'address', 'dob', 'id_number', 'id_issued_date', 'id_expiry_date']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'id_issued_date': forms.DateInput(attrs={'type': 'date'}),
            'id_expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }