from django import forms
from .models import Sender

class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        fields = '__all__'
