from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import TahunPelajaran
from datetime import datetime

@receiver(pre_save, sender=TahunPelajaran)
def update_status_tahun(sender, instance, **kwargs):
    tahun_awal = int(instance.Tahun_Pelajaran.split('/')[0])
    tahun_sekarang = datetime.now().year
    instance.status = tahun_awal >= tahun_sekarang