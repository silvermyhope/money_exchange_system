from django.db import models

class Sender(models.Model):
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    date_of_birth = models.DateField()
    id_number = models.CharField(max_length=50, unique=True)
    id_issued_date = models.DateField()
    id_expiry_date = models.DateField()

    def __str__(self):
        return f"{self.full_name} - {self.id_number}"