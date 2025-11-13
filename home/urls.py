from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Mijozlar
    path('mijoz/', views.mijoz_list, name='mijoz_list'),
    path('mijoz/create/', views.mijoz_create, name='mijoz_create'),
    path('mijoz/edit/<int:pk>/', views.mijoz_edit, name='mijoz_edit'),
    path('mijoz/delete/<int:pk>/', views.mijoz_delete, name='mijoz_delete'),

    # Avtolar
    path('avto/', views.avto_list, name='avto_list'),
    path('avto/create/', views.avto_create, name='avto_create'),
    path('avto/edit/<int:pk>/', views.avto_edit, name='avto_edit'),
    path('avto/delete/<int:pk>/', views.avto_delete, name='avto_delete'),

    # Tashriflar
    path('tashrif/', views.tashrif_list, name='tashrif_list'),
    path('tashrif/create/', views.tashrif_create, name='tashrif_create'),
    path('tashrif/edit/<int:pk>/', views.tashrif_edit, name='tashrif_edit'),
    path('tashrif/delete/<int:pk>/', views.tashrif_delete, name='tashrif_delete'),

    path('mijozlar/export/', views.export_mijoz_excel, name='export_mijoz_excel'),
    path('avto/export/', views.export_avto_excel, name='export_avto_excel'),
    path('tashrif/export/', views.export_tashrif_excel, name='export_tashrif_excel'),

    path('export/all/', views.export_all_excel, name='export_all_excel'),

]
