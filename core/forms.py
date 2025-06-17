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
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if Sender.objects.filter(id_number=id_number).exists():
            raise forms.ValidationError("A sender with this ID number already exists.")
        return id_number