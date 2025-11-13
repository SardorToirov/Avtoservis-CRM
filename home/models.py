from django.db import models


class Mijoz(models.Model):
    telefon_raqami = models.CharField(max_length=13, unique=True, blank=True, null=True)
    ism = models.CharField(max_length=100, blank=True, null=True)
    familiya = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.ism} {self.familiya} ({self.telefon_raqami})"

    class Meta:
        managed = False
        db_table = 'Mijoz'


class Avto(models.Model):
    mijoz = models.ForeignKey('Mijoz', models.DO_NOTHING, db_column='mijoz_id', blank=True, null=True)
    model = models.CharField(max_length=150, blank=True, null=True)
    raqam = models.CharField(max_length=15, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.model} - {self.raqam}"

    class Meta:
        managed = False
        db_table = 'Avto'


class Tashrif(models.Model):
    avto = models.ForeignKey(Avto, models.DO_NOTHING, db_column='avto_id', blank=True, null=True)
    sana = models.DateField(blank=True, null=True)
    joriy_km = models.IntegerField(blank=True, null=True)
    keyingi_km = models.IntegerField(blank=True, null=True)
    keyingi_sana = models.DateField(blank=True, null=True)
    xizmatlar = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.avto.raqam if self.avto else 'Nomalum avto'} tashrifi ({self.sana})"

    class Meta:
        managed = False
        db_table = 'Tashrif'