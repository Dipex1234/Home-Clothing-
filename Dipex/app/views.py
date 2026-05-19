from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import *
from django.http import JsonResponse

import razorpay
from django.conf import settings


# Create your views here.


def about_us(request):
    return render(request, "about-us.html")


def blog(request):
    return render(request, "blog.html")


def blog_full(request):
    return render(request, "blog-full.html")


def blog_full_right(request):
    return render(request, "blog-full-right.html")


def blog_right(request):
    return render(request, "blog-right.html")


@login_required(login_url='/login/')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')

    def calculate_totals():
        subtotal = 0
        for c in Cart.objects.filter(user=request.user):
            subtotal += c.subtotal()
        shipping = 295
        grand_total = subtotal + shipping
        return subtotal, shipping, grand_total

    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":

        item_id = request.POST.get("item_id")
        action = request.POST.get("action")

        try:
            cart_item = Cart.objects.get(id=item_id, user=request.user)

            if action == "increase":
                cart_item.quantity += 1

            elif action == "decrease":
                cart_item.quantity -= 1

            if cart_item.quantity <= 0:
                cart_item.delete()
                subtotal, shipping, grand_total = calculate_totals()

                return JsonResponse({
                    "deleted": True,
                    "grand_total": grand_total
                })

            cart_item.save()

        except Cart.DoesNotExist:
            return JsonResponse({"error": "Item not found"}, status=404)

        subtotal, shipping, grand_total = calculate_totals()
        item_total = cart_item.subtotal()
        cart_count = sum(c.quantity for c in Cart.objects.filter(user=request.user))

        return JsonResponse({
            "quantity": cart_item.quantity,
            "item_total": item_total,
            "grand_total": grand_total,
            "cart_count": cart_count
        })

    items = []
    subtotal = 0

    for c in cart_items:
        total = c.subtotal()
        subtotal += total

        items.append({
            'id': c.id,
            'name': c.product.name,
            'price': c.product.price,
            'image': c.product.image.url,
            'quantity': c.quantity,
            'description': c.product.description,
            'total': total,
        })

    shipping = 295
    grand_total = subtotal + shipping

    return render(request, 'cart.html', {
        'items': items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': grand_total,
    })


@login_required(login_url='/login/')
def single_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

        if qty < 1:
            qty = 1

        if created:
            cart_item.quantity = qty
        else:
            cart_item.quantity += qty

        cart_item.save()

        return redirect('cart')

    return render(request, 'single-product.html', {'product': product})


@login_required(login_url='/login/')
def remove_cart(request, id):
    Cart.objects.filter(id=id, user=request.user).delete()

    return redirect('/cart')


@login_required(login_url='/login/')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('cart')

    subtotal = sum(item.subtotal() for item in cart_items)
    shipping = 295
    total = subtotal + shipping

    if request.method == "POST":

        payment_method = request.POST.get("payment")
        shipping = int(request.POST.get("shipping", 295))
        total = subtotal + shipping

        if payment_method == "razorpay":
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            print("TOTAL IN RUPEES:", total)
            print("TOTAL IN PAISE:", int(float(total) * 100))

            razorpay_order = client.order.create({
                "amount": int(float(total) * 100),
                "currency": "INR",
                "receipt": f"order_{request.user.id}",
                "payment_capture": 1
            })

            order = Order.objects.create(
                user=request.user,
                first_name=request.POST.get("first_name"),
                last_name=request.POST.get("last_name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                address=request.POST.get("add1"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                zipcode=request.POST.get("zipcode"),
                subtotal=subtotal,
                shipping=shipping,
                total=total,
                payment_method=payment_method,
                razorpay_order_id=razorpay_order['id'],
            )

            print("RAZORPAY PAGE OPENED")
            return render(request, "payment.html", {
                "order": order,
                "razorpay_order_id": razorpay_order['id'],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": int(total * 100),
            })

        elif payment_method == "cod":

            order = Order.objects.create(
                user=request.user,
                first_name=request.POST.get("first_name"),
                last_name=request.POST.get("last_name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                address=request.POST.get("add1"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                zipcode=request.POST.get("zipcode"),
                subtotal=subtotal,
                shipping=shipping,
                total=total,
                payment_method=payment_method,
                is_paid=False,
                status="Pending"
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            Cart.objects.filter(user=request.user).delete()

            return redirect("complete_order", id=order.id)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    })


@login_required(login_url='/login/')
def payment_success(request, id):
    print("PAYMENT SUCCESS VIEW CALLED")
    if request.method != "POST":
        return redirect("checkout")

    order = get_object_or_404(Order, id=id, user=request.user)

    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        return redirect("checkout")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        client.utility.verify_payment_signature(params_dict)

        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.is_paid = True
        order.status = "Completed"

        cart_items = Cart.objects.filter(user=request.user)

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        order.save()

        print("Payment Success Called")
        print("Cart before delete:", Cart.objects.filter(user=request.user).count())

        Cart.objects.filter(user=request.user).delete()

        return redirect('complete_order', id=order.id)

    except Exception as e:
        print("Payment verification failed:", e)
        order.status = "Failed"
        order.save()
        return redirect('checkout')


def compare(request):
    return render(request, 'compare.html')


@login_required(login_url='/login/')
def complete_order(request, id):
    order = get_object_or_404(Order, id=id)
    context = {"order": order}
    print("ORDER:", order)
    print("ITEMS:", order.items.all())

    return render(request, 'complete-order.html', context)


def contact_us(request):
    return render(request, 'contact-us.html')


def faq(request):
    return render(request, 'faq.html')


def index(request):
    products = Product.objects.all()[:4]
    return render(request, 'index.html')


def index_2(request):
    return render(request, 'index-2.html')


def index_boxed_01(request):
    return render(request, 'index-boxed-01.html')


def index_boxed_02(request):
    return render(request, 'index-boxed-02.html')


def shop(request, slug=None):
    categories = Categories.objects.prefetch_related('subcategories')

    cid = request.GET.get('cid')
    scid = request.GET.get('scid')

    products = Product.objects.all()

    if cid and scid:
        products = products.filter(category_id=cid, subcategory_id=scid)
    elif cid:
        products = products.filter(category_id=cid)
    elif scid:
        products = products.filter(subcategory_id=scid)

    recent_products = Product.objects.order_by('-id')[:8]

    context = {
        'categories': categories,
        'products': products,
        'recent_products': recent_products,
    }

    return render(request, 'shop.html', context)


def my_account(request):
    return render(request, 'my-account.html')


def shop_full_grid(request):
    return render(request, "shop-full-grid.html")


def shop_full_list(request):
    return render(request, 'shop-full-list.html')


def shop_list(request):
    return render(request, 'shop-list.html')


def shop_list_right_sidebar(request):
    return render(request, 'shop-list-right-sidebar.html')


def shop_right_sidebar(request):
    return render(request, 'shop-right-sidebar.html')


def shortcode_banner(request):
    return render(request, 'shortcode-banner.html')


def shortcode_best_top_on_sale_slider(request):
    return render(request, 'shortcode-best-top-on-sale-slider.html')


def shortcode_blog_item(request):
    return render(request, 'shortcode-blog.html')


def shortcode_brad_product(request):
    return render(request, 'shortcode-brad-product.html')


def shortcode_brad_slider(request):
    return render(request, 'shortcode-brad-slider.html')


def shortcode_breadcrumb(request):
    return render(request, 'shortcode-breadcrumb.html')


def shortcode_related_product(request):
    return render(request, 'shortcode-related-product.html')


def shortcode_service(request):
    return render(request, 'shortcode-service.html')


def shortcode_skill(request):
    return render(request, 'shortcode-skill.html')


def shortcode_slider(request):
    return render(request, 'shortcode-slider.html')


def shortcode_team(request):
    return render(request, 'shortcode-team.html')


def shortcode_testimonial(request):
    return render(request, 'shortcode-testimonial.html')


def shortcode_why_choose_us(request):
    return render(request, "shortcode-why-choose-us.html")


def single_blog(request):
    return render(request, 'single-blog.html')


def single_blog_right(request):
    return render(request, 'single-blog-right.html')


@login_required(login_url='/login/')
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items
    })


@login_required(login_url='/login/')
def add_to_wishlist(request, id):
    product = get_object_or_404(Product, id=id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')


@login_required(login_url='/login/')
def remove_wishlist(request, id):
    Wishlist.objects.filter(id=id, user=request.user).delete()
    return redirect('wishlist')


def registration(request):
    if request.method == 'POST':
        un = request.POST.get('username')
        fn = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=un):
            messages.error(request, 'Username already exists.')
            return redirect('/')

        if User.objects.filter(email=email):
            messages.error(request, 'Email already exists.')
            return redirect('/')

        if len(un) > 10:
            messages.error(request, 'Username must be at least 10 characters.')
            return redirect('/')

        if not un.isalnum():
            messages.error(request, 'Username must contain only letters.')
            return redirect('/')

        user = User.objects.create_user(username=un, email=email, password=password)
        user.first_name = fn
        user.save()

        messages.success(request, 'Your account has been created!')

        return redirect('/login')

    return render(request, 'registration.html')


def Login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        di = authenticate(username=username, password=password)

        if di is not None:
            login(request, di)
            fn = di.first_name
            return render(request, 'index.html', {'fn': fn})
            # return redirect('/')
        else:
            messages.error(request, 'Bad Credentials')
            return redirect('/')
            # return redirect('/login/')

    return render(request, 'login.html')


def Logout(request):
    logout(request)
    messages.success(request, 'You are successfully logged out.')
    return redirect('/')
