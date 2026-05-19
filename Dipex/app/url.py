from django.urls import path
from . import views
from .views import single_product

urlpatterns = [
    path('', views.index, name='index'),
    path('about_us/', views.about_us),
    path('blog/', views.blog),
    path('blog_full/', views.blog_full),
    path('blog_full_right/', views.blog_full_right),
    path('blog_right/', views.blog_right),

    path('cart/', views.cart, name='cart'),
    path('single_product/<int:id>/', views.single_product, name='single_product'),
    path('remove_cart/<int:id>/', views.remove_cart, name='remove_cart'),
    path('payment_success/<int:id>/', views.payment_success, name='payment_success'),

    path('checkout/', views.checkout, name='checkout'),
    path('compare/', views.compare),
    path('complete_order/<int:id>/', views.complete_order, name='complete_order'),
    path('contact_us/', views.contact_us),
    path('faq/', views.faq),

    path('index_2/', views.index_2, name='index'),
    path('index_boxed_01/', views.index_boxed_01, name='index'),
    path('index_boxed_02/', views.index_boxed_02, name='index'),
    path('login/', views.Login),
    path('my_account/', views.my_account),

    path('shop/', views.shop, name='shop'),
    path('shop/<slug:slug>/', views.shop, name='shop_by_category'),

    path('shop_full_grid/', views.shop_full_grid),
    path('shop_full_list/', views.shop_full_list),
    path('shop_list/', views.shop_list),
    path('shop_list_right_sidebar/', views.shop_list_right_sidebar),
    path('shop_right_sidebar/', views.shop_right_sidebar),
    path('shortcode_banner/', views.shortcode_banner),
    path('shortcode_best_top_on_sale_slider/', views.shortcode_best_top_on_sale_slider),
    path('shortcode_blog_item/', views.shortcode_blog_item),
    path('shortcode_brad_product/', views.shortcode_brad_product),
    path('shortcode_brad_slider/', views.shortcode_brad_slider),
    path('shortcode_breadcrumb/', views.shortcode_breadcrumb),
    path('shortcode_related_product/', views.shortcode_related_product),
    path('shortcode_service/', views.shortcode_service),
    path('shortcode_skill/', views.shortcode_skill),
    path('shortcode_slider/', views.shortcode_slider),
    path('shortcode_team/', views.shortcode_team),
    path('shortcode_testimonial/', views.shortcode_testimonial),
    path('shortcode_why_choose_us/', views.shortcode_why_choose_us),
    path('single_blog/', views.single_blog),
    path('single_blog_right/', views.single_blog_right),

    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-wishlist/<int:id>/', views.remove_wishlist, name='remove_wishlist'),

    path('registration/', views.registration),
    path('logout/', views.Logout),
]
