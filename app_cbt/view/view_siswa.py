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
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_siswa, login_url=settings.LOGIN_URL)
@csrf_protect
def siswa(request):
    if request.method == 'POST':
        kode_soal = request.POST.get('kode_soal')

        try:
            seting_soal = models.SetingSoal.objects.get(Kode_Soal=kode_soal)

            # Validasi: kelas siswa harus sama dengan kelas dari soal
            if hasattr(request.user, 'kelas') and request.user.kelas != seting_soal.Kelas:
                nama_kelas_user = request.user.kelas.kelas  # contoh: "7A"
                nama_kelas_soal = seting_soal.Kelas.kelas   # contoh: "8A"
                messages.error(request, f"Kode ini untuk kelas {nama_kelas_soal}, sedangkan Anda dari kelas {nama_kelas_user}.")
                return redirect('cbt:siswa')

            # Validasi soal aktif
            if not seting_soal.aktif:
                nama_mapel = seting_soal.Mapel
                nama_kelas = seting_soal.Kelas.kelas  
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

    seting_soal = get_object_or_404(models.SetingSoal, Kode_Soal=kode_soal)

    # ================= VALIDASI WAKTU =================
    waktu_sekarang = timezone.now()

    if seting_soal.waktu_aktif and waktu_sekarang > seting_soal.waktu_aktif + timedelta(minutes=seting_soal.durasi_menit):
        messages.error(request, 'Waktu ujian telah habis!')
        return redirect('cbt:siswa')

    if models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal,
        Waktu_Selesai__isnull=False
    ).exists():
        return redirect('cbt:selesai_ujian', kode_soal=kode_soal)

    # ================= SOAL & JAWABAN =================
    soal_list = models.Soal_Siswa.objects.filter(Kode_Soal=seting_soal).order_by('Nomor')
    total_soal = soal_list.count()

    jawaban_pertama = models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal
    ).order_by('Waktu_Mulai').first()

    if jawaban_pertama:
        waktu_mulai = jawaban_pertama.Waktu_Mulai
        waktu_berakhir = waktu_mulai + timedelta(minutes=seting_soal.durasi_menit)
        total_detik = int((waktu_berakhir - waktu_sekarang).total_seconds())
    else:
        waktu_berakhir = waktu_sekarang + timedelta(minutes=seting_soal.durasi_menit)
        total_detik = seting_soal.durasi_menit * 60

    if total_detik <= 0:
        models.Answer.objects.filter(
            Nama_User=request.user,
            Kode_Soal=seting_soal,
            Waktu_Selesai__isnull=True
        ).update(Waktu_Selesai=waktu_berakhir)
        return redirect('cbt:selesai_ujian', kode_soal=kode_soal)

    # ================= INIT JAWABAN =================
    for soal in soal_list:
        models.Answer.objects.get_or_create(
            Nama_User=request.user,
            Kode_Soal=seting_soal,
            Nomor_Soal=soal,
            defaults={
                'Jawaban': None,
                'Jawaban_Benar': False,
                'Nilai_Siswa': 0,
                'Kelas': request.user.kelas,
                'Rombel': request.user.rombel,
                'Waktu_Mulai': waktu_sekarang if not jawaban_pertama else None
            }
        )

    jawaban_qs = models.Answer.objects.filter(
        Nama_User=request.user,
        Kode_Soal=seting_soal
    )

    jawaban_dict = {j.Nomor_Soal.id: j.Jawaban for j in jawaban_qs}

    jawaban_count = jawaban_qs.exclude(Jawaban__isnull=True).exclude(Jawaban='').count()
    semua_terjawab = jawaban_count == total_soal

    # ================= SOAL SAAT INI =================
    nomor = request.GET.get('nomor', 1)
    is_finish_page = request.GET.get('finish') == '1'

    if not is_finish_page:
        try:
            nomor = int(nomor)
            current_soal = soal_list.get(Nomor=nomor)
        except:
            current_soal = soal_list.first()
    else:
        current_soal = None

    jawaban = None
    if current_soal:
        jawaban = jawaban_qs.filter(Nomor_Soal=current_soal).first()

    # ================= POST =================
    # if request.method == 'POST':

        # SIMPAN JAWABAN
        # if current_soal:
        #     pilihan = request.POST.get('jawaban')
        #     if pilihan:
        #         jawaban.Jawaban = pilihan
        #         jawaban.Jawaban_Benar = (pilihan == current_soal.Kunci_Jawaban)
        #         jawaban.Nilai_Siswa = current_soal.Nilai if jawaban.Jawaban_Benar else 0
        #         jawaban.save()

        # NEXT
        if 'next' in request.POST:
            if current_soal and current_soal.Nomor < total_soal:
                return redirect(
                    f"{reverse('cbt:mulai_ujian', kwargs={'kode_soal': kode_soal})}?nomor={current_soal.Nomor + 1}"
                )
            else:
                return redirect(
                    f"{reverse('cbt:mulai_ujian', kwargs={'kode_soal': kode_soal})}?finish=1"
                )

        # PREV
        if 'prev' in request.POST and current_soal:
            return redirect(
                f"{reverse('cbt:mulai_ujian', kwargs={'kode_soal': kode_soal})}?nomor={current_soal.Nomor - 1}"
            )

        # FINISH
        if 'finish_exam' in request.POST:
            if semua_terjawab:
                return redirect('cbt:selesai_ujian', kode_soal=kode_soal)
            else:
                messages.error(request, 'Masih ada soal yang belum dijawab.')
                return redirect(
                    f"{reverse('cbt:mulai_ujian', kwargs={'kode_soal': kode_soal})}?finish=1"
                )

    # ================= CONTEXT =================
    context = {
        'seting_soal': seting_soal,
        'current_soal': current_soal,
        'soal_list': soal_list,
        'jawaban': jawaban,
        'jawaban_dict': jawaban_dict,
        'total_soal': total_soal,
        'jawaban_count': jawaban_count,
        'semua_terjawab': semua_terjawab,
        'is_finish_page': is_finish_page,
        'total_detik': total_detik,
        'waktu_berakhir': waktu_berakhir.isoformat(),
    }

    return render(request, 'siswa/mulai_ujian.html', context)





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_siswa, login_url=settings.LOGIN_URL)
@csrf_protect
def autosave_jawaban(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    soal_id = request.POST.get('soal_id')
    kode_soal = request.POST.get('kode_soal')
    jawaban = request.POST.get('jawaban')

    if not all([soal_id, kode_soal]):
        return JsonResponse({'status': 'invalid'}, status=400)

    try:
        answer = models.Answer.objects.get(
            Nama_User=request.user,
            Kode_Soal__Kode_Soal=kode_soal,
            Nomor_Soal_id=soal_id
        )

        if jawaban:
            answer.Jawaban = jawaban
            answer.save(update_fields=['Jawaban', 'Jawaban_Benar', 'Nilai_Siswa', 'Terakhir_Diubah'])

        return JsonResponse({
            'status': 'ok',
            'updated': timezone.now().isoformat()
        })

    except models.Answer.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)







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





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda u: u.is_siswa, login_url=settings.LOGIN_URL)
@require_POST
def submit_batch_jawaban(request):
    """Kirim batch jawaban (dipanggil setiap 10 detik)"""
    try:
        data = json.loads(request.body)
        kode_soal = data.get("kode_soal")
        jawaban_batch = data.get("jawaban", {})

        if not kode_soal or not jawaban_batch:
            return JsonResponse({"status": "error", "message": "Data tidak valid"}, status=400)

        seting_soal = get_object_or_404(models.SetingSoal, Kode_Soal=kode_soal)
        updated_count = 0
        
        with transaction.atomic():
            for soal_id, pilihan in jawaban_batch.items():
                try:
                    soal = models.Soal_Siswa.objects.get(id=soal_id, Kode_Soal=seting_soal)
                    
                    answer, created = models.Answer.objects.update_or_create(
                        Nama_User=request.user,
                        Kode_Soal=seting_soal,
                        Nomor_Soal=soal,
                        defaults={
                            "Jawaban": pilihan,
                            "Jawaban_Benar": pilihan == soal.Kunci_Jawaban,
                            "Nilai_Siswa": soal.Nilai if pilihan == soal.Kunci_Jawaban else 0,
                            "Terakhir_Diubah": timezone.now(),
                            "Kelas": request.user.kelas,
                            "Rombel": request.user.rombel
                        }
                    )
                    updated_count += 1
                    
                except models.Soal_Siswa.DoesNotExist:
                    continue

        return JsonResponse({
            "status": "ok", 
            "message": f"{updated_count} jawaban berhasil disimpan",
            "count": updated_count
        })
        
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda u: u.is_siswa, login_url=settings.LOGIN_URL)
@require_POST
def submit_semua_jawaban(request):
    """Submit semua jawaban sekaligus (dipanggil saat klik selesai)"""
    try:
        data = json.loads(request.body)
        kode_soal = data.get("kode_soal")
        semua_jawaban = data.get("jawaban", {})

        if not kode_soal:
            return JsonResponse({"status": "error", "message": "Kode soal tidak valid"}, status=400)

        seting_soal = get_object_or_404(models.SetingSoal, Kode_Soal=kode_soal)
        updated_count = 0
        
        # Waktu selesai (sama untuk semua)
        waktu_selesai = timezone.now()
        
        with transaction.atomic():
            # 1. Update semua jawaban yang dikirim
            for soal_id, pilihan in semua_jawaban.items():
                try:
                    soal = models.Soal_Siswa.objects.get(id=soal_id, Kode_Soal=seting_soal)
                    
                    # Cek apakah jawaban sudah ada dan sama
                    existing = models.Answer.objects.filter(
                        Nama_User=request.user,
                        Kode_Soal=seting_soal,
                        Nomor_Soal=soal
                    ).first()
                    
                    if existing and existing.Jawaban == pilihan:
                        # Jika sama, hanya update waktu selesai
                        existing.Waktu_Selesai = waktu_selesai
                        existing.save()
                        continue
                    
                    # Jika berbeda atau belum ada, buat/update
                    answer, created = models.Answer.objects.update_or_create(
                        Nama_User=request.user,
                        Kode_Soal=seting_soal,
                        Nomor_Soal=soal,
                        defaults={
                            "Jawaban": pilihan,
                            "Jawaban_Benar": pilihan == soal.Kunci_Jawaban,
                            "Nilai_Siswa": soal.Nilai if pilihan == soal.Kunci_Jawaban else 0,
                            "Terakhir_Diubah": waktu_selesai,
                            "Kelas": request.user.kelas,
                            "Rombel": request.user.rombel,
                            "Waktu_Selesai": waktu_selesai
                        }
                    )
                    updated_count += 1
                    
                except models.Soal_Siswa.DoesNotExist:
                    continue
            
            # 2. Pastikan semua record untuk ujian ini memiliki Waktu_Selesai
            models.Answer.objects.filter(
                Nama_User=request.user,
                Kode_Soal=seting_soal,
                Waktu_Selesai__isnull=True
            ).update(Waktu_Selesai=waktu_selesai)

        return JsonResponse({
            "status": "ok", 
            "message": f"Semua jawaban berhasil disimpan",
            "updated_count": updated_count
        })
        
    except Exception as e:
        print(f"Error in submit_semua_jawaban: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


