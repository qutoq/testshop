from decimal import Decimal
from django.conf import settings
from shop.models import Item

def display(price: Decimal) -> str:
    return "{0:.2f}".format(price / 100)

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, item: Item, quantity: int = 1, update_quantity: bool = False):
        item_id = str(item.id)
        if item_id not in self.cart:
            self.cart[item_id] = {
                'name': item.name, 
                'quantity': 0, 
                'price': str(item.price)
            }
        
        if update_quantity:
            self.cart[item_id]['quantity'] = quantity
        else:
            self.cart[item_id]['quantity'] += quantity
            
        self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, item: Item):
        item_id = str(item.id)
        if item_id in self.cart:
            del self.cart[item_id]
            self.save()

    def remove_all(self):
        self.cart = self.session[settings.CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        item_ids = [int(item_id) for item_id in self.cart.keys()]
        items = Item.objects.filter(id__in=item_ids)
        
        items_dict = {str(item.id): item for item in items}
        
        for item_id, item_data in self.cart.items():
            if item_id in items_dict:
                item = items_dict[item_id]
                price = Decimal(item_data['price'])
                quantity = item_data['quantity']
                total_price = price * quantity
                
                yield {
                    'item': item,
                    'name': item.name,
                    'price': price,
                    'quantity': quantity,
                    'total_price': total_price,
                    'display_price': display(price),
                    'display_total_price': display(total_price),
                }

    def __len__(self):
        return sum(item_data['quantity'] for item_data in self.cart.values())

    def get_total_price(self) -> str:
        total = sum(
            Decimal(item_data['price']) * item_data['quantity'] 
            for item_data in self.cart.values()
        )
        return display(total)

    def clear(self):
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.session.modified = True