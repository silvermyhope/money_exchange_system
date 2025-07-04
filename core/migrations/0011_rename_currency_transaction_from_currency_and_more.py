# Generated by Django 5.2.3 on 2025-07-01 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_transaction_receipt_transaction_updated_at_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='currency',
            new_name='from_currency',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='amount',
            new_name='sending_amount',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='service_fee',
            new_name='service_charge',
        ),
        migrations.AddField(
            model_name='transaction',
            name='exchange_rate',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
        ),
    ]
