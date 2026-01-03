from decimal import Decimal

from django.db import models
from apps.catalog.models import Item


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PAID = 'paid', 'Paid'
        CANCELED = 'canceled', 'Canceled'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )

    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.pk}'

    @property
    def subtotal(self) -> Decimal:
        return sum(
            (item.total_price for item in self.items.all()),
            Decimal('0.00')
        )

    @property
    def total(self) -> Decimal:
        total = self.subtotal

        for discount in self.discounts.all():
            total -= discount.apply(total)

        for tax in self.taxes.all():
            total += tax.apply(total)

        return max(total, Decimal('0.00'))

    @property
    def total_in_cents(self) -> int:
        return int(self.total * Decimal('100'))


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.item} x {self.quantity}'

    @property
    def total_price(self) -> Decimal:
        return self.item.price * self.quantity


class Discount(models.Model):
    class Type(models.TextChoices):
        FIXED = 'fixed', 'Fixed'
        PERCENT = 'percent', 'Percent'

    order = models.ForeignKey(
        Order,
        related_name='discounts',
        on_delete=models.CASCADE
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def apply(self, amount: Decimal) -> Decimal:
        if self.type == self.Type.FIXED:
            return min(self.value, amount)

        return amount * (self.value / Decimal('100'))


class Tax(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='taxes',
        on_delete=models.CASCADE
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Tax percent'
    )

    def apply(self, amount: Decimal) -> Decimal:
        return amount * (self.rate / Decimal('100'))
