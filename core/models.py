from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone


class Sender(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    dob = models.DateField()
    id_number = models.CharField(max_length=50, unique=True)
    id_issued_date = models.DateField()
    id_expiry_date = models.DateField()

    def __str__(self):
        return f"{self.full_name} - {self.id_number}"
    
class Receiver(models.Model):
    sender = models.ForeignKey(Sender, on_delete=models.CASCADE, related_name='receivers')
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.country})"
    

class ExchangeRate(models.Model):
    date = models.DateField(default=timezone.now)
    from_currency = models.CharField(max_length=10)
    to_currency = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        unique_together = ('date', 'from_currency', 'to_currency')

    def __str__(self):
        return f"{self.from_currency} to {self.to_currency} ({self.date}): {self.rate}"


class Transaction(models.Model):
    sender = models.ForeignKey(Sender, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(Receiver, on_delete=models.CASCADE, related_name='received_transactions')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    exchanged_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ])
    pin = models.CharField(max_length=6, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_pin(self):
        return ''.join(random.choices(string.digits, k=6))

    def calculate_exchange_and_fee(self):
        today = timezone.now().date()
        try:
            rate_obj = ExchangeRate.objects.get(date=today, from_currency=self.currency, to_currency='USD')
            self.exchanged_amount = self.amount * rate_obj.rate
            self.service_fee = self.amount * 0.05  # 5% fee example
        except ExchangeRate.DoesNotExist:
            self.exchanged_amount = None
            self.service_fee = None

    def save(self, *args, **kwargs):
        if not self.pin:
            self.pin = self.generate_pin()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.amount} {self.currency})"