from django.contrib import admin

from .models import *

# eeeee
# Register your models here.
# https://razorpay.me/@dipexmakvana

admin.site.register(Categories)
admin.site.register(Subcategories)
admin.site.register(Product)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'payment_method', 'status', 'is_paid', 'created_at']
    inlines = [OrderItemInline]


admin.site.register(OrderItem)
