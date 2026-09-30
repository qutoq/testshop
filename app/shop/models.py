from django.db import models
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator

class Item(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование товара')
    image = models.ImageField(upload_to='items/', blank=True, null=True, verbose_name='Изображение')
    description = models.TextField(max_length=1000, blank=True, null=True, verbose_name='Описание')
    price = models.IntegerField(default=0, verbose_name='Цена (в центах)')

    def get_display_price(self) -> str:
        return "{0:.2f}".format(self.price / 100)

    def get_absolute_url(self):
        return reverse('shop:item_view', kwargs={'id': self.id})

    def __str__(self):
        return f"{self.name} | ${self.get_display_price()}"

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['-id']


class Discount(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name='Название купона')
    percent_off = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        verbose_name='Процент скидки'
    )

    class Meta:
        verbose_name = 'купон'
        verbose_name_plural = 'купоны'

    def __str__(self):
        return f"{self.name} - {self.percent_off}%"


class Tax(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name='Название налога')
    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Процент налога'
    )
    stripe_id = models.CharField(max_length=100, blank=True, verbose_name='Stripe Tax ID')

    class Meta:
        verbose_name = 'налог'
        verbose_name_plural = 'налоги'

    def __str__(self):
        return f"{self.name} - {self.value}%"


class Order(models.Model):
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    paid = models.BooleanField(default=False, verbose_name='Оплачен')
    tax = models.ForeignKey(Tax, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT, verbose_name='Налог')
    discount = models.ForeignKey(Discount, null=True, blank=True, default=None, on_delete=models.SET_DEFAULT, verbose_name='Купон')

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created']

    def get_total_cost(self) -> int:
        return sum(item.get_cost() for item in self.items.all())

    def __str__(self):
        return f"Заказ #{self.id} ({'Оплачен' if self.paid else 'Не оплачен'})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name='Заказ')
    item = models.ForeignKey(Item, related_name='order_items', on_delete=models.CASCADE, verbose_name='Товар')
    price = models.IntegerField(verbose_name='Цена на момент покупки (в центах)')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'позиция товара'
        verbose_name_plural = 'позиции товаров'

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"

    def get_cost(self) -> int:
        return self.price * self.quantity