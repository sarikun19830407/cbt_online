from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import TahunPelajaran,Matapelajaran, Kelas, Rombel_kelas, DaftarNilai,SetingSoal, SEMESTER,settings
from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

@receiver(pre_save, sender=TahunPelajaran)
def update_status_tahun(sender, instance, **kwargs):
    tahun_awal = int(instance.Tahun_Pelajaran.split('/')[0])
    tahun_sekarang = datetime.now().year
    instance.status = tahun_awal >= tahun_sekarang



