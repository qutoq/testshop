from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ItemSitemap

sitemaps = {
    'items': ItemSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('cart/', include('cart.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]