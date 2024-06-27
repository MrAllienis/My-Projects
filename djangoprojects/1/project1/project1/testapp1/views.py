from django.shortcuts import render, redirect
from . models import Mebel
from . forms import UpdateItemForm
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.core.paginator import Paginator

# Create your views here.

def show_all(request):
    mebels = Mebel.objects.all().order_by("-price")
    paginator = Paginator(mebels, per_page=30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'testapp1\show_all.html',
        {'mebels': mebels, 'page_obj': page_obj},
    )

def show_all_admin(request):
    form = UpdateItemForm()
    mebels = Mebel.objects.all().order_by("-price")
    paginator = Paginator(mebels, per_page=10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'testapp1\show_admin_item.html',
        {'form': form,
         'mebels': mebels,
         'page_obj': page_obj}
    )

def show_item(request, item_id):
    try:
        item = Mebel.objects.get(pk=item_id)
    except:
        item = None
    return render(
        request,
        'testapp1\show_item.html',
        {'item': item}
    )

def update_item(request, item_id):
    if request.method == 'POST':
        new_description = dict(request.POST).get('description', '')
        new_price = dict(request.POST).get('price', '')
        item = Mebel.objects.filter(pk=item_id).update(
            price = float(new_price[0]),
            description = new_description[0]
        )
    return redirect('items_admin')

def delete_item(request, item_id):
    Mebel.objects.filter(pk=item_id).delete()
    return redirect('items_admin')

def main(request):
    return redirect('main')

def page_not_found(request, *args, **kwargs):
    return redirect('main')


def login(request):
    return render(request, 'registration/login.html')


# def logout(request):
#     return render(request, 'registration/logout.html')


class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'




