from django import forms
from .models import Avto, Mijoz, Tashrif


class AvtoForms(forms.ModelForm):
    class Meta:
        model = Avto
        fields = "__all__"


class MijozForms(forms.ModelForm):
    class Meta:
        model = Mijoz
        fields = "__all__"


class TashrifForms(forms.ModelForm):
    class Meta:
        model = Tashrif
        fields = "__all__"
        widgets = {
            'sana': forms.DateInput(attrs={'type': 'date'}),
            'keyingi_sana': forms.DateInput(attrs={'type': 'date'}),
        }
