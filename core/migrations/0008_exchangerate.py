# Generated by Django 5.2.3 on 2025-06-28 22:01

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_transaction_receiver'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('from_currency', models.CharField(max_length=10)),
                ('to_currency', models.CharField(max_length=10)),
                ('rate', models.DecimalField(decimal_places=4, max_digits=10)),
            ],
            options={
                'unique_together': {('date', 'from_currency', 'to_currency')},
            },
        ),
    ]
