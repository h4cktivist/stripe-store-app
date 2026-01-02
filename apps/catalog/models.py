from decimal import Decimal

from django.db import models


class Item(models.Model):
    class Currency(models.TextChoices):
        USD = 'usd', 'USD'
        EUR = 'eur', 'EUR'

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price in major currency units (e.g. 10.99)'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def price_in_cents(self) -> int:
        return int(self.price * Decimal('100'))
