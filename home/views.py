from django.shortcuts import render, redirect, get_object_or_404
from .models import Mijoz, Avto, Tashrif
from .forms import MijozForms, AvtoForms, TashrifForms
from django.db.models import Q

# Dashboard
def home(request):
    context = {
        'mijoz_soni': Mijoz.objects.count(),
        'avto_soni': Avto.objects.count(),
        'tashrif_soni': Tashrif.objects.count(),
    }
    return render(request, 'home.html', context)

# ===== Mijozlar =====
def mijoz_list(request):
    search_query = request.GET.get('q', '')
    if search_query:
        mijozlar = Mijoz.objects.filter(
            Q(ism__icontains=search_query) |
            Q(familiya__icontains=search_query) |
            Q(telefon_raqami__icontains=search_query)
        )
    else:
        mijozlar = Mijoz.objects.all()
    context = {'mijozlar': mijozlar, 'search_query': search_query}
    return render(request, 'mijoz_list.html', context)

def mijoz_create(request):
    form = MijozForms(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('mijoz_list')
    return render(request, 'mijoz_form.html', {'form': form})

def mijoz_edit(request, pk):
    mijoz = get_object_or_404(Mijoz, pk=pk)
    form = MijozForms(request.POST or None, instance=mijoz)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('mijoz_list')
    return render(request, 'mijoz_form.html', {'form': form})

def mijoz_delete(request, pk):
    mijoz = get_object_or_404(Mijoz, pk=pk)
    mijoz.delete()
    return redirect('mijoz_list')


# ===== Avtolar =====
def avto_list(request):
    search_query = request.GET.get('q', '')
    if search_query:
        avtolar = Avto.objects.filter(
            Q(model__icontains=search_query) |
            Q(raqam__icontains=search_query) |
            Q(mijoz__ism__icontains=search_query)
        )
    else:
        avtolar = Avto.objects.all()
    context = {'avtolar': avtolar, 'search_query': search_query}
    return render(request, 'avto_list.html', context)

def avto_create(request):
    form = AvtoForms(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('avto_list')
    return render(request, 'avto_form.html', {'form': form})

def avto_edit(request, pk):
    avto = get_object_or_404(Avto, pk=pk)
    form = AvtoForms(request.POST or None, instance=avto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('avto_list')
    return render(request, 'avto_create.html', {'form': form})

def avto_delete(request, pk):
    avto = get_object_or_404(Avto, pk=pk)
    avto.delete()
    return redirect('avto_list')


# ===== Tashriflar =====
def tashrif_list(request):
    search_query = request.GET.get('q', '')
    if search_query:
        tashriflar = Tashrif.objects.filter(
            Q(avto__raqam__icontains=search_query) |
            Q(avto__model__icontains=search_query) |
            Q(avto__mijoz__ism__icontains=search_query) |
            Q(sana__icontains=search_query)
        )
    else:
        tashriflar = Tashrif.objects.all()
    context = {'tashriflar': tashriflar, 'search_query': search_query}
    return render(request, 'tashrif_list.html', context)

def tashrif_create(request):
    form = TashrifForms(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('tashrif_list')
    return render(request, 'tashrif_form.html', {'form': form})

def tashrif_edit(request, pk):
    tashrif = get_object_or_404(Tashrif, pk=pk)
    form = TashrifForms(request.POST or None, instance=tashrif)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('tashrif_list')
    return render(request, 'tashrif_form.html', {'form': form})

def tashrif_delete(request, pk):
    tashrif = get_object_or_404(Tashrif, pk=pk)
    tashrif.delete()
    return redirect('tashrif_list')
