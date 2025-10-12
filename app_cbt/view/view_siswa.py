from django.shortcuts import render, redirect,get_object_or_404
from multiprocessing import context
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required,user_passes_test,  permission_required
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.db import transaction
from django.contrib.sessions.models import Session

from django.urls import reverse
import os
from django.http import FileResponse, HttpResponse, JsonResponse,Http404
import tempfile
from django.utils.timezone import now
from django.db import IntegrityError
import re
from django.views.decorators.cache import never_cache

from app_cbt import models
from app_cbt import forms_staff
from django.http import HttpResponse, Http404
import time 
from django.db.models import Count, Case, When, IntegerField
from app_cbt import forms
import xlrd
from django.core.files.storage import default_storage
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from io import BytesIO
from tempfile import NamedTemporaryFile
import openpyxl
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from openpyxl import load_workbook
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_siswa, login_url=settings.LOGIN_URL)
@csrf_protect
def siswa(request):
    if request.method == 'POST':
        kode_soal = request.POST.get('kode_soal')

        try:
            seting_soal = models.SetingSoal.objects.get(Kode_Soal=kode_soal)

            # Validasi: kelas siswa harus sama dengan kelas dari soal
            if hasattr(request.user, 'Kelas') and request.user.Kelas != seting_soal.Kelas:
                nama_kelas_user = request.user.Kelas.Kelas  # contoh: "7A"
                nama_kelas_soal = seting_soal.Kelas.Kelas   # contoh: "8A"
                messages.error(request, f"Kode ini untuk kelas {nama_kelas_soal}, sedangkan Anda dari kelas {nama_kelas_user}.")
                return redirect('cbt:siswa')

            # Validasi soal aktif
            if not seting_soal.aktif:
                nama_mapel = seting_soal.Mapel
                nama_kelas = seting_soal.Kelas.Kelas  
                messages.error(request, f"Soal {nama_mapel} kelas {nama_kelas} belum diaktifkan.")
                return redirect('cbt:siswa')

            # Jika sudah pernah mengerjakan, langsung lanjut
            if models.Answer.objects.filter(Nama_User=request.user, Kode_Soal=seting_soal).exists():
                return redirect(reverse('cbt:mulai_ujian', kwargs={'kode_soal': seting_soal.Kode_Soal}))

            # Belum mengerjakan, lanjut ke mulai ujian
            return redirect(reverse('cbt:mulai_ujian', kwargs={'kode_soal': seting_soal.Kode_Soal}))

        except models.SetingSoal.DoesNotExist:
            messages.error(request, 'Kode ujian tidak valid!')

    return render(request, 'siswa/home_siswa.html')









@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_siswa, login_url=settings.LOGIN_URL)
@csrf_protect
def mulai_ujian(request, kode_soal):
    # Ambil data ujian
    seting_soal = get_object_or_404(models.SetingSoal, Kode_Soal=kode_soal)
    

    waktu_sekarang = timezone.now()
    if seting_soal.waktu_aktif and waktu_sekarang > seting_soal.waktu_aktif + timedelta(minutes=seting_soal.durasi_menit):
        messages.error(request, 'Waktu ujian telah habis!')
        return redirect(reverse('cbt:siswa'))
    
    # Cek apakah ujian sudah diselesaikan
    if models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal,
        Waktu_Selesai__isnull=False
    ).exists():
        messages.error(request, f'Anda sudah menyelesaikan ujian {seting_soal.Mapel}')
        return redirect(reverse('cbt:selesai_ujian', kwargs={'kode_soal': seting_soal.Kode_Soal}))
    
    # Pengaturan waktu ujian
    waktu_sekarang = timezone.now()
    jawaban_pertama = models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal
    ).order_by('Waktu_Mulai').first()
    
    # Hitung waktu tersisa
    if jawaban_pertama:
        waktu_mulai = jawaban_pertama.Waktu_Mulai
        waktu_berakhir = waktu_mulai + timedelta(minutes=seting_soal.durasi_menit)
        waktu_tersisa = waktu_berakhir - waktu_sekarang
        
        # Jika waktu sudah habis
        if waktu_tersisa.total_seconds() <= 0:
            models.Answer.objects.filter(
                Nama_User=request.user,
                Kode_Soal=seting_soal,
                Waktu_Selesai__isnull=True
            ).update(Waktu_Selesai=waktu_berakhir)
            messages.error(request, 'Waktu ujian telah habis!')
            return redirect(reverse('cbt:selesai_ujian', kwargs={'kode_soal': seting_soal.Kode_Soal}))
        
        total_detik = int(waktu_tersisa.total_seconds())
    else:
        # Jika baru memulai ujian
        waktu_berakhir = waktu_sekarang + timedelta(minutes=seting_soal.durasi_menit)
        total_detik = seting_soal.durasi_menit * 60
    
    # Ambil daftar soal
    soal_list = models.Soal_Siswa.objects.filter(Kode_Soal=seting_soal).order_by('Nomor')
    
    # Inisialisasi jawaban untuk semua soal
    for soal in soal_list:
        models.Answer.objects.get_or_create(
            Nama_User=request.user,
            Kode_Soal=seting_soal,
            Nomor_Soal=soal,
            defaults={
                'Jawaban': None,
                'Jawaban_Benar': False,
                'Nilai_Siswa': 0,
                'Kelas': request.user.Kelas,
                'Rombel': request.user.Rombel,
                'Waktu_Mulai': waktu_sekarang if not jawaban_pertama else None
            }
        )
    
    # Ambil semua jawaban yang sudah ada
    jawaban_dict = {
        jawaban.Nomor_Soal.id: jawaban.Jawaban
        for jawaban in models.Answer.objects.filter(
            Nama_User=request.user,
            Kode_Soal=seting_soal
        )
    }

    # Hitung jumlah jawaban yang sudah diisi
    jawaban_count = sum(1 for j in jawaban_dict.values() if j)
    semua_terjawab = jawaban_count == soal_list.count()
    
    # Ambil soal saat ini
    nomor_soal = request.GET.get('nomor', 1)
    try:
        nomor_soal = int(nomor_soal)
        current_soal = models.Soal_Siswa.objects.get(Kode_Soal=seting_soal, Nomor=nomor_soal)
    except (ValueError, models.Soal_Siswa.DoesNotExist):
        current_soal = soal_list.first()
        nomor_soal = current_soal.Nomor if current_soal else 1

    # Ambil jawaban dari current soal
    jawaban = models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal,
        Nomor_Soal=current_soal
    ).first()
    
    # Handle POST request
    if request.method == 'POST':
        if 'finish' in request.POST:
            if semua_terjawab:
                return redirect(reverse('cbt:selesai_ujian', kwargs={'kode_soal': seting_soal.Kode_Soal}))
            else:
                messages.error(request, 'Anda belum menjawab semua soal!')
                return redirect(reverse('cbt:mulai_ujian', kwargs={'kode_soal': seting_soal.Kode_Soal}))

        # Proses penyimpanan jawaban
        jawaban_pilihan = request.POST.get('jawaban')
        if jawaban:
            jawaban.Jawaban = jawaban_pilihan
            jawaban.save()
            
            # Update jawaban benar dan nilai jika kunci jawaban tersedia
            if hasattr(current_soal, 'Kunci'):
                jawaban.Jawaban_Benar = (jawaban_pilihan == current_soal.Kunci)
                jawaban.Nilai_Siswa = seting_soal.Mapel.Bobot_Nilai if jawaban.Jawaban_Benar else 0
                jawaban.save()

        # Navigasi soal
        if 'next' in request.POST:
            next_soal = models.Soal_Siswa.objects.filter(
                Kode_Soal=seting_soal,
                Nomor__gt=current_soal.Nomor
            ).order_by('Nomor').first()
            if next_soal:
                return redirect(f"{reverse('cbt:mulai_ujian', kwargs={'kode_soal': kode_soal})}?nomor={next_soal.Nomor}")
        
        elif 'prev' in request.POST:
            prev_soal = models.Soal_Siswa.objects.filter(
                Kode_Soal=seting_soal,
                Nomor__lt=current_soal.Nomor
            ).order_by('-Nomor').first()
            if prev_soal:
                return redirect(f"{reverse('cbt:mulai_ujian', kwargs={'kode_soal': kode_soal})}?nomor={prev_soal.Nomor}")

    # Persiapkan context
    context = {
        'seting_soal': seting_soal,
        'current_soal': current_soal,
        'soal_list': soal_list,
        'jawaban': jawaban,
        'total_soal': soal_list.count(),
        'jawaban_count': jawaban_count,
        'semua_terjawab': semua_terjawab,
        'jawaban_dict': jawaban_dict,
        'total_detik': total_detik,
        'waktu_berakhir': waktu_berakhir.isoformat(),
        'durasi_menit': seting_soal.durasi_menit,
    }
    
    return render(request, 'siswa/mulai_ujian.html', context)









@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_siswa, login_url=settings.LOGIN_URL)
@csrf_protect
def selesai_ujian(request, kode_soal):
    # Ambil setting soal
    seting_soal = get_object_or_404(models.SetingSoal, Kode_Soal=kode_soal)
    

    # Ambil semua jawaban siswa terkait kode soal
    jawaban_siswa = models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal
    ).select_related("Nomor_Soal")

    # Hitung jumlah soal dari SetingSoal
    total_soal = models.Soal_Siswa.objects.filter(Kode_Soal=seting_soal).count()

    # Hitung nilai dan jumlah jawaban benar
    jawaban_benar = 0
    total_nilai = 0

    for ans in jawaban_siswa:
        if ans.Jawaban_Benar:
            nilai_soal = ans.Nomor_Soal.Nilai or 0
            total_nilai += nilai_soal
            jawaban_benar += 1

    # Hitung nilai maksimal
    nilai_maksimal = sum(
        soal.Nilai or 0
        for soal in models.Soal_Siswa.objects.filter(Kode_Soal=seting_soal)
    )

    # Hitung skor: (total_nilai * 100) / nilai_maksimal
    skor = round((total_nilai * 100) / nilai_maksimal, 2) if nilai_maksimal > 0 else 0

    # Catat waktu selesai ujian
    jawaban_siswa.filter(Waktu_Selesai__isnull=True).update(Waktu_Selesai=now())

    context = {
        "judul": "CBT - Ujian Selesai",
        "seting_soal": seting_soal,
        "total_nilai": total_nilai,
        "nilai_maksimal": nilai_maksimal,
        "skor": skor,
        "jawaban_benar": jawaban_benar,
        "total_soal": total_soal,
    }

    return render(request, "siswa/selesai_ujian.html", context)





