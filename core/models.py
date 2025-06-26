from django.db import models
from django.contrib.auth.models import User

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

class Transaction(models.Model):
    sender = models.ForeignKey(Sender, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(Receiver, on_delete=models.CASCADE, related_name='received_transactions')
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cashier_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ])
    pin = models.CharField(max_length=6, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pin:
            self.pin = self.generate_pin()
        super().save(*args, **kwargs)

    def generate_pin(self):
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.amount} {self.currency})"