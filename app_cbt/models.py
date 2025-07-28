from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser, User
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils.text import slugify
from bs4 import BeautifulSoup
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

import random
import secrets
import string

from django.conf import settings

from django.utils.html import strip_tags

# Create your models here.

TINKAT_CHOICES =(
        ('SD/MI','SD/MI'),
        ('SMP/MTS','SMP/MTS'),
        ('SMA/MA','SMA/MA'),
        )
sm =(
        ('Genap','Genap'),
        ('Ganjil','Ganjil'),
        )



KURIKULUM =(
    ('K13','K13'),
    ('Merdeka Belajar','Merdeka Belajar'),
)

ROMBEL_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F'),
        ('G', 'G'),
        ('H', 'H'),
        ('I', 'I'),
        ('J', 'J'),
        ('K', 'K'),
        ('L', 'L'),
        ('M', 'M'),
        ('N', 'N'),
    ]

def buat_nomor_baru():
    alphabet = string.ascii_letters + string.digits  # Kombinasi huruf besar, kecil, dan angka
    alphabet = string.ascii_uppercase + string.digits
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for i in range(10))  # Token sepanjang 10 karakter


# ..........................................##################################.......................................................................


class SEMESTER (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL,  editable=False,  on_delete = models.CASCADE)
    Semester = models.CharField(
        choices = sm,
        default = '',
        max_length=30
        ) 
    status = models.BooleanField(default=False)

    
    def __str__(self):
        return self.Semester


class TahunPelajaran(models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE)
    Tahun_Pelajaran = models.CharField(max_length=9)
    status = models.BooleanField(default=False)
    tanggal_penetapan = models.DateField(default=timezone.now)
    semester = models.ForeignKey(SEMESTER,   on_delete = models.CASCADE)

    def clean(self):
        if self.status and TahunPelajaran.objects.filter(status=True).exclude(id=self.id).exists():
            raise ValidationError("Hanya boleh ada satu tahun pelajaran aktif!")

    def save(self, *args, **kwargs):
        if self.status:
            # Set semua tahun pelajaran lainnya menjadi tidak aktif
            TahunPelajaran.objects.exclude(id=self.id).update(status=False)
        
            self.full_clean()  # tetap validasi
        super().save(*args, **kwargs)


    def __str__(self):
        return self.Tahun_Pelajaran
    



    
    
class Lembaga (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL,  editable=False,  on_delete = models.CASCADE)
    Nama_Lembaga = models.CharField(max_length=100)
    Ketua_panitia = models.CharField(max_length=100)
    NIP = models.CharField (max_length=30,blank=True, null=True)
    NPSN = models.CharField(max_length=8)
    Alamat = models.TextField()
    Tikatan_Satuan_Lembaga =models.CharField(
        choices = TINKAT_CHOICES,
        default = '',
        max_length=30
        ) 
    satatus = models.BooleanField(default=True)

    def __str__(self):
        return str(self.Nama_Lembaga)

# untuk tinkatan kelas 1-MI/SD samapi dengan 12-SMA/MA
class Kelas (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete = models.CASCADE)
    Nama_Lembaga = models.ForeignKey(Lembaga,   on_delete = models.CASCADE)
    Kelas = models.CharField(max_length=2, unique=True)
    status = models.BooleanField(default=True)
    
    def __str__(self):
        return self.Kelas
    
    
class Rombel_kelas (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete = models.CASCADE)
    Nama_Lembaga = models.ForeignKey(Lembaga,   on_delete = models.CASCADE)
    Kelas = models.ForeignKey(Kelas,on_delete = models.CASCADE,)
    Rombel = models.CharField(max_length=5)

    def __str__(self):
        return self.Rombel

class Pengguna (AbstractUser):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete = models.CASCADE, blank=True, null=True)
    Nama = models.CharField(max_length=100)
    Nama_Lembaga = models.ForeignKey(Lembaga,  on_delete = models.CASCADE, blank=True, null=True)
    Tikatan_Satuan_Lembaga =models.CharField(
        choices = TINKAT_CHOICES,
        default = '',
        max_length=30
        )
    Kelas= models.ForeignKey(Kelas,  on_delete = models.CASCADE, blank=True, null=True)
    Rombel = models.ForeignKey(Rombel_kelas,on_delete = models.CASCADE, blank=True, null=True)
    is_siswa = models.BooleanField("Siswa",  default= False)
    

    def __str__(self):
        return self.Nama

    
class KurikulumLembaga (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False,  on_delete = models.CASCADE)
    semster = models.ForeignKey(SEMESTER,on_delete = models.CASCADE)
    Tahun_pelajaran = models.ForeignKey(TahunPelajaran,on_delete = models.CASCADE)
    Kurikulum = models.CharField(choices = KURIKULUM,
        default = '',
        max_length=30
        )

    def __str__(self):
        return self.Kurikulum    

class Matapelajaran(models.Model):
    Nama_User= models.ForeignKey(settings.AUTH_USER_MODEL,  editable=False,  on_delete = models.CASCADE)
    Nama_Lembaga = models.ForeignKey(Lembaga,   on_delete = models.CASCADE)
    Nama_Mapel = models.CharField(max_length=100)
    
    
        
    def __str__(self):
        return self.Nama_Mapel
    




class SetingSoal(models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL,  editable=False,  on_delete = models.CASCADE)
    Nama_Lembaga = models.ForeignKey(Lembaga,   on_delete = models.CASCADE)
    Kode_Soal = models.CharField(
        max_length = 10,
        editable=False,
        default=buat_nomor_baru
    )
    Kelas = models.ForeignKey(Kelas,on_delete = models.CASCADE)
    Mapel = models.ForeignKey(Matapelajaran,on_delete = models.CASCADE)
    Semester = models.CharField(
        choices = sm,
        default = '',
        max_length=30
        )
    Tahun_Pelajaran = models.ForeignKey(TahunPelajaran, on_delete = models.CASCADE)
    aktif = models.BooleanField(default=False)  
    waktu_aktif = models.DateTimeField(blank=True, null=True)
    durasi_menit = models.PositiveIntegerField()
    arsip_soal = models.BooleanField(default=False)


    class Meta:
        ordering = ['Kelas_id']

    def __str__(self):
        return str(self.Kode_Soal)
    
    def waktu_berakhir(self):
        if self.waktu_aktif and self.durasi_menit:
            return self.waktu_aktif + timedelta(minutes=self.durasi_menit)
        return None

    def is_waktu_berjalan(self):
        if self.waktu_aktif and self.durasi_menit:
            now = timezone.now()
            return self.waktu_aktif <= now <= self.waktu_berakhir()
        return False


    def generate_unique_token():
        alphabet = string.ascii_letters + string.digits
        alphabet = string.ascii_uppercase + string.digits
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        while True:
            token = ''.join(secrets.choice(alphabet) for i in range(10))
            if not SetingSoal.objects.filter(token=token).exists():  # Cek apakah token sudah ada di database
                return token




class DaftarNilai (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete = models.CASCADE)
    Nama_Lembaga = models.ForeignKey(Lembaga,   on_delete = models.CASCADE)
    Kelas = models.ForeignKey(Kelas,on_delete = models.CASCADE,)
    Rombel = models.ForeignKey(Rombel_kelas,on_delete = models.CASCADE,)
    Mapel = models.ForeignKey(Matapelajaran,on_delete = models.CASCADE,)
    Semester = models.CharField(
        choices = sm,
        default = '',
        max_length=30
        )
    Tahun_Pelajaran = models.ForeignKey(TahunPelajaran, on_delete = models.CASCADE)

    def __str__(self):
        return self.Mapel


    
KUNCI = (
    ('A','A',),
    ('B','B',),
    ('C','C',),
    ('D','D',),
)

# di immput di akun guru
class Soal_Siswa (models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL,  editable=False,  on_delete = models.CASCADE)
    Kode_Soal = models.ForeignKey(SetingSoal, on_delete = models.CASCADE)
    Mapel = models.ForeignKey(Matapelajaran, on_delete = models.CASCADE)
    Kelas = models.ForeignKey(Kelas, on_delete = models.CASCADE)
    Nomor = models.IntegerField()
    Soal = RichTextUploadingField()
    A = RichTextUploadingField()
    B = RichTextUploadingField()
    C = RichTextUploadingField()
    D = RichTextUploadingField()
    
    
    
    Kunci_Jawaban = models.CharField(
        choices=KUNCI,
        default = 0,
        max_length=1
        )
    Nilai = models.PositiveIntegerField(blank=True, null=True)


    def __str__(self):
        return f"Soal {self.Nomor}"
    


class Answer(models.Model):
    Nama_User = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE)
    Kode_Soal = models.ForeignKey(SetingSoal, on_delete=models.CASCADE)
    Nomor_Soal = models.ForeignKey(Soal_Siswa, on_delete=models.CASCADE)
    Kelas= models.ForeignKey(Kelas,  on_delete = models.CASCADE)
    Rombel= models.ForeignKey(Rombel_kelas, on_delete = models.CASCADE)
    Jawaban = models.CharField(
        max_length=1,
        choices=KUNCI,
        blank=True,
        null=True
    )
    Jawaban_Benar = models.BooleanField(default=False)
    Nilai_Siswa = models.PositiveIntegerField(blank=True, null=True)
    Waktu_Mulai = models.DateTimeField(auto_now_add=True)
    Waktu_Selesai = models.DateTimeField(blank=True, null=True)
    Terakhir_Diubah = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('Nama_User', 'Kode_Soal', 'Nomor_Soal')

    def save(self, *args, **kwargs):
        # Otomatis set jawaban benar jika sesuai dengan kunci
        if self.Jawaban == self.Nomor_Soal.Kunci_Jawaban:
            self.Jawaban_Benar = True
            self.Nilai_Siswa = self.Nomor_Soal.Nilai
        else:
            self.Jawaban_Benar = False
            self.Nilai_Siswa = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.Nama_User.username} - {self.Kode_Soal.Kode_Soal} - Soal {self.Nomor_Soal.Nomor}"
    
    def save(self, *args, **kwargs):
        # Otomatis set jawaban benar dan ambil nilai dari Soal_Siswa
        if self.Jawaban == self.Nomor_Soal.Kunci_Jawaban:
            self.Jawaban_Benar = True
            self.Nilai_Siswa = self.Nomor_Soal.Nilai  # Ambil nilai dari soal terkait
        else:
            self.Jawaban_Benar = False
            self.Nilai_Siswa = 0
        super().save(*args, **kwargs)
    
    

