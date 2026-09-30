from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Item, OrderItem, Order
from cart.forms import CartAddItemForm, OrderForm
from cart.cart import Cart
from .stripy import new_stripe_session, add_tax

def main(request):
    items = Item.objects.all()
    return render(request, 'shop/test.html', {'items': items})

def item_view(request, id):
    item = get_object_or_404(Item, id=id)
    cart_item_form = CartAddItemForm()
    return render(request, 'shop/item_view.html', {'item': item, 'cart_item_form': cart_item_form})

@require_POST
def new_order(request):
    cart = Cart(request)
    if not cart:
        return redirect('shop:main')

    form = OrderForm(request.POST)
    if not form.is_valid():
        return redirect('cart:cart_detail')

    cd = form.cleaned_data
    order = Order.objects.create(tax=cd['tax'], discount=cd['discount'])

    line_items = []
    for item in cart:
        price_data = {
            'currency': 'rub',
            'product_data': {'name': item['name']},
            'unit_amount': item['price']
        }
        line_item = {
            'price_data': price_data,
            'quantity': item['quantity']
        }
        
        if order.tax and order.tax.stripe_id:
            add_tax(order.tax)
            line_item['tax_rates'] = [order.tax.stripe_id]
            
        line_items.append(line_item)
        OrderItem.objects.create(
            order=order, 
            item=item['item'], 
            price=item['price'], 
            quantity=item['quantity']
        )

    session = new_stripe_session(line_items, order.discount, order.tax, order, "/cart/")
    return redirect(session.url, code=303)

@require_POST
def buy_item(request, id):
    item = get_object_or_404(Item, id=id)
    order = Order.objects.create()
    
    OrderItem.objects.create(order=order, item=item, price=item.price, quantity=1)

    product_data = {'name': item.name}
    if item.image and settings.DOMAIN != "http://127.0.0.1:8000":
        product_data['images'] = [f"{settings.DOMAIN}{item.image.url}"]

    line_items = [{
        'price_data': {
            'currency': 'rub',
            'product_data': product_data,
            'unit_amount': item.price,
        },
        'quantity': 1,
    }]

    session = new_stripe_session(line_items, None, None, order, f"/item/{id}/")
    return redirect(session.url, code=303)

def success(request):
    cart = Cart(request)
    cart.clear()
    return render(request, "shop/success.html")