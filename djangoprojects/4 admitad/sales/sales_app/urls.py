from django.urls import path, re_path
from . import views

app_name = 'sales_app'



urlpatterns = [
    path('', views.main, name='main'),
    path('coupons/', views.redirect_to, name='redirect_to'),
    path('shops', views.show_shops, name='shops'),
    path('shops/<int:shop_id>', views.show_shop_item, name='shop_item'),
    path('categories', views.show_categories, name='categories'),
    path('category/<int:category_id>', views.category_shops, name='category_shops'),
    path('shops_products', views.shops_products, name='shops_products'),
    path('all', views.all, name='all'),
    path('shops/<int:shop_id>/categories', views.category_view, name='category_view'),
    path('shops/<int:shop_id>/categories/<str:category1>', views.category_view, name='category_view'),
    path('shops/<int:shop_id>/categories/<str:category1>/<str:category2>', views.category_view, name='category_view'),
    path('shops/<int:shop_id>/categories/<str:category1>/<str:category2>/<str:category3>', views.category_view, name='category_view'),
    path('shops/<int:shop_id>/categories/<str:category1>/<str:category2>/<str:category3>/<str:category4>', views.category_view, name='category_view'),
    # re_path(r'^shop/(?P<shop_id>\d+)/product/(?P<product_id>.+)/$', views.product_item, name='product_item'),
    # path('load-more-products/', views.load_more_products, name='load_more_products'),

]
