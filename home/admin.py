from django.contrib import admin
from .models import Mijoz, Avto, Tashrif


# --- 1. Mijozlar uchun admin klassi ---
@admin.register(Mijoz)
class MijozAdmin(admin.ModelAdmin):
    # Admin panel jadvalida ko'rsatiladigan maydonlar
    list_display = ('telefon_raqami', 'ism', 'familiya')

    # Qidiruv maydonlari (Qidiruv faqat shu maydonlar bo'yicha ishlaydi)
    search_fields = ('telefon_raqami', 'ism', 'familiya')

    # Filtrlar (kerak bo'lsa)
    list_filter = ('familiya',)

    # Ma'lumotlarni tartiblash (Telefon raqami bo'yicha)
    ordering = ('telefon_raqami',)

    # Mijoz tafsilotlari sahifasida yozish tartibi
    fieldsets = (
        (None, {
            'fields': ('telefon_raqami', 'ism', 'familiya'),
        }),
    )


# --- 2. Avtomobillar uchun admin klassi ---
@admin.register(Avto)
class AvtoAdmin(admin.ModelAdmin):
    # Jadvalda Mijoz ismini ko'rsatish uchun maxsus usul
    list_display = ('raqam', 'model', 'mijoz_ismi_familiyasi', 'mijoz_telefoni')

    # Qidiruv: Avto raqami, modeli va Mijoz telefoni bo'yicha
    search_fields = ('raqam', 'model', 'mijoz__telefon_raqami', 'mijoz__ism', 'mijoz__familiya')

    # Filtrlar: Avto modeli bo'yicha
    list_filter = ('model',)

    # Mijozning ismini chiqaruvchi usul
    def mijoz_ismi_familiyasi(self, obj):
        if obj.mijoz:
            return f"{obj.mijoz.ism} {obj.mijoz.familiya or ''}".strip()
        return "Noma'lum"

    mijoz_ismi_familiyasi.short_description = 'Mijoz'

    # Mijozning telefon raqamini chiqaruvchi usul
    def mijoz_telefoni(self, obj):
        return obj.mijoz.telefon_raqami if obj.mijoz else 'N/A'

    mijoz_telefoni.short_description = 'Tel. raqami'


# --- 3. Tashriflar uchun admin klassi ---
@admin.register(Tashrif)
class TashrifAdmin(admin.ModelAdmin):
    # Tashriflarni Avto raqami, sana va joriy km bo'yicha ko'rsatish
    list_display = ('avto_raqami', 'sana', 'joriy_km', 'keyingi_km', 'keyingi_sana')

    # Filtrlar: Sana va keyingi xizmat muddati bo'yicha
    list_filter = ('sana', 'keyingi_sana')

    # Qidiruv: Avto raqami va model nomi bo'yicha
    search_fields = ('avto__raqam', 'avto__model')

    # Tashrif sahifasida 'sana' maydonini faqat o'qish uchun qilish
    readonly_fields = ('sana',)

    # Avto raqamini chiqaruvchi usul
    def avto_raqami(self, obj):
        return obj.avto.raqam if obj.avto else 'N/A'

    avto_raqami.short_description = 'Avto Raqami'

    # Sanani teskari tartibda joylashtirish (eng yangi tashriflar yuqorida)
    ordering = ('-sana',)