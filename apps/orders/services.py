from apps.orders.models import Order, OrderItem
from apps.catalog.models import Item


def get_or_create_order(request) -> Order:
    order_id = request.session.get('order_id')

    if order_id:
        try:
            return Order.objects.get(
                id=order_id,
                status=Order.Status.DRAFT
            )
        except Order.DoesNotExist:
            pass

    order = Order.objects.create()
    request.session['order_id'] = order.id
    return order


def add_item_to_order(order: Order, item: Item, quantity: int = 1):
    order_item, created = OrderItem.objects.get_or_create(
        order=order,
        item=item,
        defaults={'quantity': quantity},
    )

    if not created:
        order_item.quantity += quantity
        order_item.save()
