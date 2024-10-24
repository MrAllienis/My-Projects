from django.shortcuts import render, redirect, get_object_or_404
from . models import Shop, Product, Coupon, CategoryShop, LinkClick
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.db.models import Count, Q, F, ExpressionWrapper, IntegerField, Case, When, Value, BooleanField, Func
from django.core.paginator import Paginator
from django.db.models.functions import Ceil, Length
from django.db.models.expressions import RawSQL
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db import connection



def all(request):
    search_query = request.GET.get('search', '').strip()
    sort_order = request.GET.get('sort', 'name')
    # Получение текущей страницы из GET-параметра
    page_number = int(request.GET.get('page', 1))
    limit = 50  # Ограничение на 10 записей

    if page_number > 1:
        offset = limit*(page_number-1)
    else:
        offset = 0


    if search_query:
        query = SearchQuery(search_query, config='russian')

        if sort_order == '-sale':
            vector = SearchVector('name', config='russian')
            products = Product.objects.filter(search=query).annotate(
                rank=SearchRank(vector, query),  # Ранг релевантности
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).filter(rank__gt=0).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-sale', '-starts_with', '-rank')[offset:offset + limit]
            # products = Product.objects.filter(search=query).only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by('-sale')[offset:offset+limit]
            # for word in search_query.split(' '):
            #     # search_pattern = f'%{word}%'
            #     products += f".filter(name__icontains='{word}')"
            # products += f".only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by('{sort_order}')[offset:offset+limit]"
            # products = eval(products)
        elif sort_order == 'last_update':
            vector = SearchVector('name', config='russian')
            # products = Product.objects.select_related('shop').filter(search=query).only('name', 'price', 'old_price', 'image', 'shop_id', 'shop__last_update', 'sale', 'url').order_by('-shop__last_update')[offset:offset+limit]
            products = Product.objects.select_related('shop').filter(search=query).annotate(
                rank=SearchRank(vector, query),  # Ранг релевантности
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).filter(rank__gt=0).only('name', 'price', 'old_price', 'image', 'shop_id', 'shop__last_update', 'sale', 'url').order_by('-shop__last_update', '-starts_with', '-rank')[offset:offset + limit]
            # for word in search_query.split(' '):
            #     # search_pattern = f'%{word}%'
            #     products += f".filter(name__icontains='{word}')"
            # products += f".only('name', 'price', 'old_price', 'image', 'shop_id', 'shop__last_update', 'sale', 'url').order_by('-shop__last_update')[offset:offset+limit]"
            # products = eval(products)
        elif sort_order in ['price', '-price']:
            products = Product.objects.filter(search=query).annotate(
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-starts_with', sort_order)[offset:offset + limit]
        else:
            products = Product.objects.filter(search=query).annotate(
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-starts_with')[offset:offset + limit]
    else:
        if sort_order == '-sale':
            products = Product.objects.filter(price__isnull=False).only('name', 'price','old_price', 'image', 'sale', 'url').order_by(sort_order)[offset:offset + limit]
        elif sort_order == 'last_update':
            with connection.cursor() as cursor:
                # SET для настройки сессии
                cursor.execute("SET enable_material TO off;")
                # ORM-запрос
                products = Product.objects.select_related('shop').only(
                    'name', 'price', 'old_price', 'image', 'shop_id',
                    'shop__last_update', 'sale', 'url'
                ).order_by('-shop__last_update')[offset:offset + limit]
        elif sort_order in ['price', '-price']:
            products = Product.objects.only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by(sort_order)[offset:offset + limit]
        else:
            products = Product.objects.only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by()[offset:offset + limit]

    count = len(products)
    page_obj = products
    if count >= limit:
        has_next = page_number + 1
    else:
        has_next = None

    if page_number > 1:
        has_previous = page_number - 1
    else:
        has_previous = None

    return render(request, 'sales_app/all.html', {'page_obj': page_obj, 'has_previous': has_previous,
        'has_next': has_next, 'number': page_number, 'order': sort_order})


def show_shops(request):
    query = request.GET.get('search')

    # Optimize the query using select_related for ForeignKey or OneToOne relationships
    if query:
        shops = Shop.objects.filter(name__icontains=query).only('shop_id', 'category', 'name', 'image').order_by("name").prefetch_related('category')
    else:
        shops = Shop.objects.all().only('shop_id', 'category', 'name', 'image').order_by("name").prefetch_related('category')

    return render(
        request,
        'sales_app/show_shops.html',
        {'shops': shops},
    )


def show_shop_item(request, shop_id):
    shop = Shop.objects.get(pk=shop_id)
    coupons = Coupon.objects.filter(shop=shop)
    for coupon in coupons:
        if coupon.discount is not None:
            if coupon.discount[-1] == '%':
                if int(coupon.discount[:-1]) >= 30:
                    coupon.name = f"1{coupon.name}"
                elif coupon.code in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН', None]:
                    coupon.name = f"2{coupon.name}"
                else:
                    coupon.name = f"3{coupon.name}"
            elif coupon.code in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН', None]:
                coupon.name = f"2{coupon.name}"
            else:
                coupon.name = f"3{coupon.name}"
        elif coupon.code in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН', None]:
            coupon.name = f"2{coupon.name}"
        else:
            coupon.name = f"3{coupon.name}"

    return render(
        request,
        'sales_app/show_shop_item.html',
        {'shop': shop, 'coupons': coupons},
    )


def show_categories(request):
    shops = Shop.objects.all().order_by("name")
    categories = CategoryShop.objects.all().annotate(store_count=Count('shops')).order_by("name")
    return render(
        request,
        'sales_app/show_categories.html',
        {'shops': shops, 'categories': categories}
        ,)


def category_shops(request, category_id):
    # Получаем значение из поля поиска
    search_query = request.GET.get('search')
    category = CategoryShop.objects.get(pk=category_id)
    if search_query:
        shops = Shop.objects.filter(category=category_id).filter(name__icontains=search_query)
    else:
        shops = Shop.objects.filter(category=category_id)

    return render(request, 'sales_app/category_shops.html', {'shops': shops, 'search_query': search_query, 'category': category})


def shops_products(request):
    query = request.GET.get('search')
    if query:
        shops = Shop.objects.filter(name__icontains=query).only('shop_id', 'category', 'name', 'image').order_by("name").prefetch_related('category')
    else:
        shops = Shop.objects.all().only('shop_id', 'category', 'name', 'image').order_by("name").prefetch_related('category')

    return render(
        request,
        'sales_app/shop_products.html',
        {'shops': shops},
    )



def get_filtered_products(shop, search_query, sort_order, page_number, category1=None, category2=None, category3=None, category4=None):
    filters = {
        'shop': shop,
    }
    if category1:
        filters['category1'] = category1
    if category2:
        filters['category2'] = category2
    if category3:
        filters['category3'] = category3
    if category4:
        filters['category4'] = category4


    limit = 50  # Ограничение на 10 записей

    if page_number > 1:
        offset = limit * (page_number - 1)
    else:
        offset = 0

    if search_query:
        if sort_order == '-sale':
            products = "Product.objects.annotate(has_sale=Case(When(sale__isnull=False, then=True), default=False, output_field=BooleanField())).filter(price__isnull=False)"
            for word in search_query.split(' '):
                # search_pattern = f'%{word}%'
                products += f".filter(**filters)"
                products += f".filter(name__icontains='{word}')"
            products += f".only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by('-has_sale', '{sort_order}')[offset:offset+limit]"
            products = eval(products)
        elif sort_order == 'last_update':
            products = "Product.objects.select_related('shop')"
            for word in search_query.split(' '):
                # search_pattern = f'%{word}%'
                products += f".filter(**filters)"
                products += f".filter(name__icontains='{word}')"
            products += f".only('name', 'price', 'old_price', 'image', 'shop__last_update', 'sale', 'url').order_by('-shop__last_update')[offset:offset+limit]"
            products = eval(products)
        else:
            products = "Product.objects"
            for word in search_query.split(' '):
                # search_pattern = f'%{word}%'
                products += f".filter(**filters)"
                products += f".filter(name__icontains='{word}')"
            products += f".only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by('{sort_order}')[offset:offset+limit]"
            products = eval(products)
    else:
        if sort_order == '-sale':
            products = Product.objects.annotate(has_sale=Case(When(sale__isnull=False, then=True), default=False, output_field=BooleanField())).filter(**filters, price__isnull=False).only('name', 'price','old_price', 'image', 'sale', 'url').order_by('-has_sale', sort_order)[offset:offset + limit]
        elif sort_order == 'last_update':
            products = Product.objects.select_related('shop').filter(**filters).only('name', 'price', 'old_price', 'image', 'shop__last_update', 'sale', 'url').order_by('-shop__last_update')[offset:offset + limit]
        else:
            products = Product.objects.filter(**filters).only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by(sort_order)[offset:offset + limit]

    count = len(products)
    page_obj = products
    if count >= limit:
        has_next = page_number + 1
    else:
        has_next = None

    if page_number > 1:
        has_previous = page_number - 1
    else:
        has_previous = None

    return page_obj, has_next, has_previous, sort_order


def category_view(request, shop_id):
    shop = Shop.objects.get(pk=shop_id)
    search_query = request.GET.get('search', '')
    sort_order = request.GET.get('sort', 'name')
    # Получение текущей страницы из GET-параметра
    page_number = int(request.GET.get('page', 1))
    limit = 50  # Ограничение на 10 записей

    if page_number > 1:
        offset = limit * (page_number - 1)
    else:
        offset = 0

    if search_query:
        query = SearchQuery(search_query, config='russian')

        if sort_order == '-sale':
            vector = SearchVector('name', config='russian')
            products = Product.objects.filter(shop_id=shop_id).filter(search=query).annotate(
                rank=SearchRank(vector, query),  # Ранг релевантности
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).filter(rank__gt=0).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-sale', '-starts_with', '-rank')[offset:offset + limit]
        elif sort_order == 'last_update':
            vector = SearchVector('name', config='russian')
            # products = Product.objects.select_related('shop').filter(search=query).only('name', 'price', 'old_price', 'image', 'shop_id', 'shop__last_update', 'sale', 'url').order_by('-shop__last_update')[offset:offset+limit]
            products = Product.objects.filter(shop_id=shop_id).select_related('shop').filter(search=query).annotate(
                rank=SearchRank(vector, query),  # Ранг релевантности
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).filter(rank__gt=0).only('name', 'price', 'old_price', 'image', 'shop_id', 'shop__last_update', 'sale',
                                      'url').order_by('-shop__last_update', '-starts_with', '-rank')[
                       offset:offset + limit]
        elif sort_order in ['price', '-price']:
            vector = SearchVector('name', config='russian')
            products = Product.objects.filter(shop_id=shop_id).filter(search=query).annotate(
                rank=SearchRank(vector, query),  # Ранг релевантности
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).filter(rank__gt=0).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by(sort_order, '-starts_with', '-rank')[offset:offset + limit]
        else:
            products = Product.objects.filter(shop_id=shop_id).filter(search=query).annotate(
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-starts_with')[offset:offset + limit]
    else:
        if sort_order == '-sale':
            products = Product.objects.filter(shop_id=shop_id).filter(price__isnull=False).only('name', 'price', 'old_price', 'image', 'sale',
                                                                        'url').order_by(sort_order)[
                       offset:offset + limit]
        elif sort_order in ['price', '-price']:
            products = Product.objects.filter(shop_id=shop_id).only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by(sort_order)[
                       offset:offset + limit]
        else:
            products = Product.objects.filter(shop_id=shop_id).only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by()[
                       offset:offset + limit]

    count = len(products)
    page_obj = products
    if count >= limit:
        has_next = page_number + 1
    else:
        has_next = None

    if page_number > 1:
        has_previous = page_number - 1
    else:
        has_previous = None

    return render(request, 'sales_app/products.html', {'page_obj': page_obj, 'has_previous': has_previous,
                                                  'has_next': has_next, 'number': page_number, 'order': sort_order, 'shop': shop})


# def product_item(request, shop_id, product_id):
#     shop = Shop.objects.get(pk=shop_id)
#     product = Product.objects.get(pk=product_id)
#     return render(request, 'sales_app/product_item.html', {'product': product, 'shop': shop})


def redirect_to(request):
    yclid = request.GET.get('yclid')
    # if yclid:
    #     LinkClick.objects.create(yclid=yclid, clicked_at=timezone.now())

    return redirect(f'https://t.me/coupons186_bot/?start={yclid}')


def main(request):
    shops = Shop.objects.all().only('image')
    return render(request, 'sales_app/main.html', {'shops': shops})