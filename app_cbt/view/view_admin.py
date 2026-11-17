from django.shortcuts import render, redirect,get_object_or_404
from multiprocessing import context
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
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
import subprocess
from django.http import FileResponse, HttpResponse, JsonResponse,Http404
import tempfile
from django.utils.timezone import now
from django.db import IntegrityError
import re
from django.views.decorators.cache import never_cache

from app_cbt import models
from app_cbt import forms
import csv
import xlrd
import xlwt
from openpyxl import load_workbook as load_xlsx
from django.http import HttpResponse, Http404
import time 
from django.db.models import Count, Case, When, IntegerField, F
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static
from django.utils import timezone
from django.db.models import Q
from concurrent.futures import ThreadPoolExecutor
import random
import string



from django.core.management import call_command
from utils.encryption import encrypt_file, cleanup_files, decrypt_file





@csrf_protect
@never_cache
def app_cbt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # ✅ Batasi hanya untuk siswa
            if user.is_siswa:
                # Ambil semua session yang masih aktif
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                for session in sessions:
                    data = session.get_decoded()
                    if data.get('_auth_user_id') == str(user.id):
                        # Kalau user sudah punya session aktif → tolak login baru
                        if session.session_key != request.session.session_key:
                            messages.error(request, "Akun ini sedang aktif di perangkat lain. Anda tidak boleh login.")
                            return redirect("/")  

            # ✅ Kalau lolos pengecekan, izinkan login
            login(request, user)

            if user.is_superuser:
                return redirect(reverse("cbt:home"))
            elif user.is_staff:
                return redirect(reverse("cbt:staff"))
            elif user.is_siswa:
                return redirect(reverse('cbt:siswa'))
            else:
                return redirect('/DasboardSuperuser')

        else:
            messages.error(request, 'Gagal Login Username atau Password salah')
            return redirect("/")

    context = {
        "data": "CBT",
        "judul": "CBT"
    }
    return render(request, 'login.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def home (request):
    lembaga = models.Lembaga.objects.filter(status=True).first()
    Data = models.TahunPelajaran.objects.filter(status=True)
    Siswa = models.Pengguna.objects.filter(is_siswa=True, Nama_Lembaga=lembaga)
    rombel = models.Rombel_kelas.objects.filter(Nama_Lembaga=lembaga)
    contex={
        "data":"Home",
        "judul":"CBT",
        "Data":Data,
        "siswa":Siswa.count(),
        "rombel":rombel.count(),
        "icon":"bi bi-house"
    }
    return render (request, 'super_admin/home.html', contex)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def bersihkan_file_temp(request):
    folder_temp = os.path.join(settings.MEDIA_ROOT, 'temp')
    count = 0
    for filename in os.listdir(folder_temp):
        file_path = os.path.join(folder_temp, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            count += 1
    messages.success(request, f"{count} file dihapus dari folder temp.")
    return redirect(reverse('cbt:home'))






@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def update_userlogin(request):
    form = forms.FormUpdateSuperAdmin(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.instance.Nama_User = request.user
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:home'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Update user login",
        "NamaForm": "Form update user login",
        "judul":"CBT",
        "link":reverse("cbt:home"),
        "form":form,
        'icon':"bi bi-pen"
        }
    return render (request, 'super_admin/form_user.html', context)






@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def kurikulum_lembaga(request):
    Data = models.KurikulumLembaga.objects.filter(Nama_User=request.user)

    # Add additional context
    context={
        "Data":Data,
        "data": "Data Kurikulum Lembaga",
        "judul": "CBT-Kurikulum Lembaga",
        "icon":"bi bi-book"
    }
    
    return render(request, 'super_admin/kurikulum_lembaga.html', context)


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_kurikulum(request):
    form = forms.Form_kurikulum(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.instance.Nama_User = request.user
            form.instance.status = True
            form.save()
            messages.add_message(request, messages.INFO, f'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:kurikulum_lembaga'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Tambah Kurikulum",
        "NamaForm": "Form Tambah Kurikulum",
        "judul":"CBT-user staff",
        "link":reverse("cbt:kurikulum_lembaga"),
        "form":form,
        "icon":"bi bi-plus-circle"
        }
    return render (request, 'super_admin/form.html', context)


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Hapus_kurikulum (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID kurikulum tidak valid.")
        return redirect(reverse('cbt:kurikulum_lembaga'))
    
    try:
        Data = get_object_or_404(models.KurikulumLembaga, id=pk)
    except Http404:
        messages.error(request, "Data kurikulum tidak ditemukan.")
        return redirect(reverse('cbt:kurikulum_lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa hapus data Anda sendiri.")
            return redirect (reverse('cbt:kurikulum_lembaga'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, f'{Data} telah berhasil di hapus')
        return redirect (reverse('cbt:kurikulum_lembaga'))
    return redirect (reverse('cbt:kurikulum_lembaga'))





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_kurikulum (request, pk):
    
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID kurikulum tidak valid.")
        return redirect(reverse('cbt:kurikulum_lembaga'))
    
    try:
        Data = get_object_or_404(models.KurikulumLembaga, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:kurikulum_lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:kurikulum_lembaga'))
    
    form = forms.Form_kurikulum(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, f'{Data} telah berhasil diubah')
            return redirect(reverse('cbt:kurikulum_lembaga'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah Kurikulum",
        "NamaForm": "Form ubah Kurikulum",
        "judul":"CBT-Kurikulum Lembaga",
        "link":reverse("cbt:kurikulum_lembaga"),
        "form":form,
        'icon':"bi bi-pen"
        }
    return render (request, 'super_admin/form.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def jenis_ujian(request):

    # Ambil KEY dari choices
    VALID_JENIS = [key for key, _ in models.JENIS_UJIAN]

    if request.method == 'POST':
        selected_jenis = request.POST.get('jenis_ujian', '').strip()

        if selected_jenis in VALID_JENIS:

            # ❗ Nonaktifkan semua jenis ujian milik user
            models.Jenis_Ujian.objects.filter(
                Nama_User=request.user
            ).update(status=False)

            # Ambil / buat data
            obj, created = models.Jenis_Ujian.objects.get_or_create(
                Nama_User=request.user,
                Jenis_Ujian=selected_jenis
            )

            # Aktifkan
            obj.status = True
            obj.save()

            messages.success(
                request,
                f"Jenis ujian {obj.get_Jenis_Ujian_display()} berhasil diaktifkan."
            )
            return redirect(reverse("cbt:jenis_ujian"))

        else:
            messages.error(request, "Pilihan jenis ujian tidak valid.")

    # Ambil jenis ujian aktif
    current = models.Jenis_Ujian.objects.filter(
        Nama_User=request.user,
        status=True
    ).first()

    context = {
        "data": "Jenis Ujian",
        "judul": "CBT",
        "icon": "bi bi-bookmark-check",
        "current_choice": current.Jenis_Ujian if current else '',
        "choices": models.JENIS_UJIAN,
    }

    return render(request, 'super_admin/jenis_ujian.html', context)







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def semester(request):
    if request.method == 'POST':
        selected_semester = request.POST.get('semester', '').strip()

        if selected_semester in ['Genap','Ganjil' ]:  # Validasi semester yang dipilih valid
            # ❗ Set semua semester milik user menjadi tidak aktif (status=False)
            models.SEMESTER.objects.filter(Nama_User=request.user).update(status=False)

            # Ambil atau buat entri baru
            semester_instance, created = models.SEMESTER.objects.get_or_create(
                Nama_User=request.user,
                Semester=selected_semester,
            )

            # Tandai sebagai aktif
            semester_instance.status = True
            semester_instance.save()

            messages.success(request, f"Semester {selected_semester} berhasil diaktifkan.")
            return redirect(reverse("cbt:semester"))
        else:
            messages.error(request, "Pilihan semester tidak valid.")
    
    # Ambil semester yang aktif (jika ada)
    current_semester = models.SEMESTER.objects.filter(Nama_User=request.user, status=True).first()
    current_choice = current_semester.Semester if current_semester else ''
    
    context = {
        "data": "Semester",
        "judul": "PPDB",
        'current_choice': current_choice,
        "icon":"bi bi-bookmark-check"
    }
    return render(request, 'super_admin/semester_form.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tahun_pelajaran(request):
    Data = models.TahunPelajaran.objects.filter(Nama_User=request.user)
    context ={
        "data":"Tahun Pelajaran",
        "judul":"CBT-Tahun Pelajaran",
        "Data":Data,
        'icon':"bi bi-calendar-check"
    }

    return render (request, 'super_admin/list_tahun_pelajaran.html', context)

@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_tahun_pelajaran(request):
    form = forms.FormTahunPeljaran(request.POST or None)
    
    if request.method == "POST":
        if form.is_valid():
            tahun_pelajaran = form.save(commit=False)
            tahun_pelajaran.Nama_User = request.user
            tahun_pelajaran.status = True
            
            # ✅ Cek semester aktif
            semester_aktif = models.SEMESTER.objects.filter(status=True).first()
            if not semester_aktif:
                messages.error(request, "Tidak ada semester aktif. Silakan tetapkan satu semester terlebih dahulu.")
            else:
                tahun_pelajaran.semester = semester_aktif
                try:
                    # ✅ Nonaktifkan semua DaftarNilai sebelumnya
                    models.DaftarNilai.objects.filter(status=True).update(status=False)

                    tahun_pelajaran.save()
                    messages.success(request, "Tahun Pelajaran berhasil ditambahkan. Semua DaftarNilai sebelumnya dinonaktifkan.")
                    return redirect(reverse('cbt:tahun_pelajaran'))
                except ValidationError as e:
                    messages.error(request, f"Validasi gagal: {e.messages}")
        else:
            messages.error(request, "Form tidak valid. Periksa kembali data yang dimasukkan.")

    context = {
        "data": "Tambah Tahun Pelajaran",
        "NamaForm": "Form Tambah Tahun Pelajran",
        "judul": "CBT",
        "link": reverse("cbt:tahun_pelajaran"),
        "form": form,
        "icon": "bi bi-plus-circle"
    }
    return render(request, 'super_admin/form.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Hapus_Tahun_Pelajaran (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID tahun pelajaran tidak valid.")
        return redirect(reverse('cbt:tahun_pelajaran'))
    try:
        Data = get_object_or_404(models.TahunPelajaran, id=pk)
    except Http404:
        messages.error(request, "Data tahun pelajaran tidak ditemukan.")
        return redirect(reverse('cbt:tahun_pelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa hapus data Anda sendiri.")
            return redirect (reverse('cbt:tahun_pelajaran'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:tahun_pelajaran'))
    return redirect (reverse('cbt:tahun_pelajaran'))




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_Tahun_Pelajaran (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID tahun pelajaran tidak valid.")
        return redirect(reverse('cbt:tahun_pelajaran'))
    try:
        Data = get_object_or_404(models.TahunPelajaran, id=pk)
    except Http404:
        messages.error(request, "Data tahun pelajaran tidak ditemukan.")
        return redirect(reverse('cbt:tahun_pelajaran'))  # Redirect ke halaman daftar pengguna

    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:tahun_pelajaran'))

    form = forms.FormTahunPeljaran(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil diubah')
            return redirect(reverse('cbt:tahun_pelajaran'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah Tahun Pelajaran",
        "NamaForm": "Form ubah Tahun Pelajaran",
        "judul":"CBT",
        "link":reverse("cbt:tahun_pelajaran"),
        "form":form,
        "icon":"bi bi-pencil"
        }
    return render (request, 'super_admin/form.html', context)






    
login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def lembaga(request):
    cari = request.POST.get('cari', request.GET.get('cari', '')) 
    items_per_page = request.GET.get('items_per_page', '30')  # Ubah ke string dulu
    
    # Jika memilih "Semua", set items_per_page ke jumlah besar
    if items_per_page == 'all':
        items_per_page = 1000000  # Angka besar untuk menampilkan semua
    else:
        try:
            items_per_page = int(items_per_page)
        except (ValueError, TypeError):
            items_per_page = 30  # Default jika invalid

    data_list = models.Lembaga.objects.filter(Nama_User=request.user)
    if cari:
        data_list = data_list.filter(Nama_Lembaga__icontains=cari)

    paginator = Paginator(data_list, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        Data = paginator.page(page_number)
    except PageNotAnInteger:
        Data = paginator.page(1)
    except EmptyPage:
        Data = paginator.page(paginator.num_pages)

    semua = str(items_per_page) if items_per_page != 1000000 else 'all'
    Data.start_index = (Data.start_index() - 1)
    jumlah = data_list.count()
    
    context = {
        "data": "Data Lembaga",
        "judul": "CBT-Lembaga",
        "Data": Data,
        "jumlah": jumlah,
        "cari": cari,
        "items_per_page": semua ,
        "lembaga": "Akun Siswa",
        "placeholder": "Username/Nama siwa",
        "icon":"bi bi-bank"
    }
    
    return render(request, 'super_admin/list_lembaga.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_lembaga(request):
    form = forms.Form_lembaga(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.instance.Nama_User = request.user
            lembaga = models.KurikulumLembaga.objects.filter(status=True).first()
            form.instance.kurikulum_lebaga=lembaga
            form.instance.status = True
            form.save()
            messages.add_message(request, messages.INFO, f'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:lembaga'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Tambah Lembaga",
        "NamaForm": "Form Tambah Lembaga",
        "judul":"CBT-user staff",
        "link":reverse("cbt:lembaga"),
        "form":form,
        "icon":"bi bi-plus-circle"
        }
    return render (request, 'super_admin/form.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Hapus_lembaga (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID lembaga tidak valid.")
        return redirect(reverse('cbt:lembaga'))
    try:
        Data = get_object_or_404(models.Lembaga, id=pk)
    except Http404:
        messages.error(request, "Data lembaga tidak ditemukan.")
        return redirect(reverse('cbt:lembaga'))  # Redirect ke halaman daftar pengguna

    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa menghapus data Anda sendiri.")
            return redirect (reverse('cbt:lembaga'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, f'{Data} telah berhasil di hapus')
        return redirect (reverse('cbt:lembaga'))
    return redirect (reverse('cbt:lembaga'))



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_lembaga (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID lembaga tidak valid.")
        return redirect(reverse('cbt:lembaga'))

    try:
        Data = get_object_or_404(models.Lembaga, id=pk)
    except Http404:
        messages.error(request, "Data lembaga tidak ditemukan.")
        return redirect(reverse('cbt:lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:lembaga'))

    form = forms.Form_lembaga(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, f'{Data} telah berhasil diubah')
            return redirect(reverse('cbt:lembaga'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : f"Hapus lembaga {Data}",
        "judul":"CBT-Lembaga",
        "judul":"CBT-Kurikulum Lembaga",
        "link":reverse("cbt:lembaga"),
        "form":form,
        'icon':"bi bi-pen"
        }
    return render (request, 'super_admin/form.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def matapelajaran(request):
    Data = models.Matapelajaran.objects.filter(Nama_User=request.user)
    context ={
        "data":"Mata Pelajaran",
        "judul":"CBT-Mapel",
        "Data":Data,
        "icon":"bi bi-list-check"
    }

    return render (request, 'super_admin/list_mapel.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_pelajaran(request):
    form = forms.MatapelajaranForm(request.POST or None)
    
    if request.method == "POST":
        # Validasi manual untuk field kosong
        has_empty_fields = False
        for field_name, field in form.fields.items():
            if field.required and not request.POST.get(field_name):
                has_empty_fields = True
                form.add_error(field_name, "Field ini wajib diisi")
        
        if has_empty_fields:
            messages.error(request, 'Silahkan tambhakan lembaga pada update user.')
        elif form.is_valid():
            form.instance.Nama_User = request.user
            lembaga_aktif = models.Lembaga.objects.filter(status = True).first()
            form.instance.Nama_Lembaga = lembaga_aktif
            form.save()
            messages.success(request, 'Data telah berhasil ditambahkan')
            return redirect(reverse('cbt:matapelajaran'))
        else:
            messages.error(request, 'Data masih salah.')
    
    context = {
        "data": "Tambah Mata Pelajaran",
        "NamaForm": "Form Mata Pelajaran",
        "judul": "CBT",
        "link": reverse("cbt:matapelajaran"),
        "form": form,
        "icon":"bi bi-plus-circle"
    }
    return render(request, 'super_admin/form.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Hapus_mapel (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID mata pelajaran tidak valid.")
        return redirect(reverse('cbt:matapelajaran'))

    try:
        Data = get_object_or_404(models.Matapelajaran, id=pk)
    except Http404:
        messages.error(request, "Data mata pelajaran tidak ditemukan.")
        return redirect(reverse('cbt:matapelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa hapus data Anda sendiri.")
            return redirect (reverse('cbt:matapelajaran'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:matapelajaran'))
    return redirect (reverse('cbt:matapelajaran'))




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_Mata_Pelajaran (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID mata pelajaran tidak valid.")
        return redirect(reverse('cbt:matapelajaran'))

    try:
        Data = get_object_or_404(models.Matapelajaran, id=pk)
    except Http404:
        messages.error(request, "Data mata pelajaran tidak ditemukan.")
        return redirect(reverse('cbt:matapelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:matapelajaran'))
    
    form = forms.MatapelajaranForm(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil diubah')
            return redirect(reverse('cbt:matapelajaran'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah Mata Pelajaran",
        "NamaForm": "Form ubah Mata Pelajaran",
        "judul":"CBT",
        "link":reverse("cbt:matapelajaran"),
        "form":form,
        'icon':"bi bi-pen"
        }
    return render (request, 'super_admin/form.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Kelas(request):
    Data = models.Kelas.objects.filter(Nama_User=request.user)
    context ={
        "data":"Kelas",
        "judul":"CBT-Kelas",
        "Data":Data,
        "icon":"bi bi-backpack3"
    }

    return render (request, 'super_admin/list_kelas.html', context)





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_kelas(request):
    form = forms.FormKelas(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            # cek lembaga aktif
            lembaga_aktif = models.Lembaga.objects.filter(status=True).first()
            if not lembaga_aktif:
                messages.error(request, "Belum ada Lembaga dengan status aktif. Silakan set dulu.")
                return redirect(reverse("cbt:tambah_kelas"))  # balik ke halaman form

            form.instance.Nama_User = request.user
            form.instance.Nama_Lembaga = lembaga_aktif
            form.instance.satatus = True
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil ditambahkan')
            return redirect(reverse('cbt:Kelas'))
        else:
            messages.error(request, 'Data masih salah.')

    context = {
        "data": "Tambah Kelas",
        "NamaForm": "Form Tambah Kelas",
        "judul": "CBT-Kelas",
        "link": reverse("cbt:Kelas"),
        "form": form,
        "icon": "bi bi-plus-circle"
    }
    return render(request, 'super_admin/form.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def hapus_kelas (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID kelas tidak valid.")
        return redirect(reverse('cbt:Kelas'))

    try:
        Data = get_object_or_404(models.Kelas, id=pk)
    except Http404:
        messages.error(request, "Data kelas tidak ditemukan.")
        return redirect(reverse('cbt:Kelas'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa hapus data Anda sendiri.")
            return redirect (reverse('cbt:Kelas'))
    
    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:Kelas'))
    return redirect (reverse('cbt:Kelas'))



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_Kelas (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID kelas tidak valid.")
        return redirect(reverse('cbt:Kelas'))

    try:
        Data = get_object_or_404(models.Kelas, id=pk)
    except Http404:
        messages.error(request, "Data kelas tidak ditemukan.")
        return redirect(reverse('cbt:Kelas'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:Kelas'))

    form = forms.FormKelas(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil diubah')
            return redirect(reverse('cbt:Kelas'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah Kelas",
        "NamaForm": "Form ubah Kelas",
        "judul":"CBT-Kelas",
        "link":reverse("cbt:Kelas"),
        "form":form,
        "icon":"bi bi-pencil"
        
        }
    return render (request, 'super_admin/form.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Rombel(request):
    Data = models.Rombel_kelas.objects.filter(Nama_User=request.user)
    context ={
        "data":"Rombel",
        "judul":"CBT-Rombel",
        "Data":Data,
        "icon":"bi bi-backpack3"
    }

    return render (request, 'super_admin/list_rombel.html', context)


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_rombel(request):
    form = forms.FormRombel(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.instance.Nama_User = request.user
            lembaga_aktif = models.Lembaga.objects.filter(status=True).first()
            form.instance.Nama_Lembaga = lembaga_aktif
            form.instance.satatus = True
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:Rombel'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Tambah Rombel",
        "NamaForm": "Form Tambah Rombel",
        "judul":"CBT-Rombel",
        "link":reverse("cbt:Rombel"),
        "form":form,
        "icon":"bi bi-plus-circle"
        }
    return render (request, 'super_admin/form.html', context)


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def hapus_rombel (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID rombel tidak valid.")
        return redirect(reverse('cbt:Rombel'))

    try:
        Data = get_object_or_404(models.Rombel_kelas, id=pk)
    except Http404:
        messages.error(request, "Data rombel tidak ditemukan.")
        return redirect(reverse('cbt:Rombel'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa hapus data Anda sendiri.")
            return redirect (reverse('cbt:matapelajaran'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:Rombel'))
    return redirect (reverse('cbt:Rombel'))



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def ubah_rombel (request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID rombel tidak valid.")
        return redirect(reverse('cbt:Rombel'))

    try:
        Data = get_object_or_404(models.Rombel_kelas, id=pk)
    except Http404:
        messages.error(request, "Data rombel tidak ditemukan.")
        return redirect(reverse('cbt:Rombel'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:matapelajaran'))

    form = forms.FormRombel(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil diubah')
            return redirect(reverse('cbt:Rombel'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah Rombel",
        "NamaForm": "Form ubah Rombel",
        "judul":"CBT-Rombel",
        "link":reverse("cbt:Rombel"),
        "form":form,
        "icon":"bi bi-pencil"
        
        }
    return render (request, 'super_admin/form.html', context)





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def user_staff(request):
    cari = request.POST.get('cari', request.GET.get('cari', '')) 
    items_per_page = request.GET.get('items_per_page', '30')  # Ubah ke string dulu
    
    # Jika memilih "Semua", set items_per_page ke jumlah besar
    if items_per_page == 'all':
        items_per_page = 1000000  # Angka besar untuk menampilkan semua
    else:
        try:
            items_per_page = int(items_per_page)
        except (ValueError, TypeError):
            items_per_page = 30  # Default jika invalid

    data_list = models.Pengguna.objects.filter(is_staff=True, is_superuser=False, Nama_User=request.user)
    if cari:
        data_list = data_list.filter(Nama_Pengguna__icontains=cari) | data_list.filter(username__icontains=cari)

    paginator = Paginator(data_list, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        Data = paginator.page(page_number)
    except PageNotAnInteger:
        Data = paginator.page(1)
    except EmptyPage:
        Data = paginator.page(paginator.num_pages)
        
    Data.start_index = (Data.start_index() - 1)
    jumlah = data_list.count()
    
    context = {
        "data": "List User Staff",
        "judul": "CBT-User Staff",
        "Tambah": "/PenggunaMadrasah",
        "Data": Data,
        "jumlah": jumlah,
        "cari": cari,
        "items_per_page": str(items_per_page) if items_per_page != 1000000 else 'all',
        "lembaga": "akun madrasah",
        "placeholder": "Nama Madrasah/NSM",
        "icon":"bi bi-database-check"
    }
    
    return render(request, 'super_admin/list_user_staff.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_user_staff(request):
    form = forms.Form_Staff(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.instance.Nama_User = request.user
            lembaga_aktif = get_object_or_404(models.Lembaga, status=True)
            form.instance.Nama_Lembaga = lembaga_aktif
            form.instance.is_staff = True
            form.save()
            messages.success(request, 'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:user_staff'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Tambah user staff",
        "NamaForm": "Form Tambah user staff",
        "judul":"CBT-user staff",
        "link":reverse("cbt:user_staff"),
        "form":form,
        "icon":"bi bi-plus-circle"
        }
    return render (request, 'super_admin/form_user.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def hapus_user_staff (request, pk):
    try:
        pk = int(pk)
    except ValueError:
        messages.error(request, "ID user staff tidak valid.")
        return redirect(reverse('cbt:user_staff'))

    try:
        Data = get_object_or_404(models.Pengguna, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_staff'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa hapus data Anda sendiri.")
            return redirect (reverse('cbt:matapelajaran'))

    if request.method == "POST":
        Data.delete()
        messages.success(request, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:user_staff'))
    return redirect (reverse('cbt:user_staff'))



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_user_staff (request, pk):
    try:
        pk = int(pk)
    except ValueError:
        messages.error(request, "ID user staff tidak valid.")
        return redirect(reverse('cbt:user_staff'))

    try:
        Data = get_object_or_404(models.Pengguna, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_staff'))  
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect (reverse('cbt:matapelajaran'))

    form = forms.Form_Ubah_Staff(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, 'Data telah berhasil diubah')
            return redirect(reverse('cbt:user_staff'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah user staff",
        "NamaForm": "Form ubah user staff",
        "judul":"CBT-user staff",
        "link":reverse("cbt:user_staff"),
        "form":form,
        "icon":"bi bi-pencil"
        }
    return render (request, 'super_admin/form_user.html', context)






login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def active_user_staff(request, pk):
    try:
        pk = int(pk)
    except ValueError:
        messages.error(request, "ID user staff tidak valid.")
        return redirect(reverse('cbt:user_staff'))  
    try:
        user_target = get_object_or_404(models.Pengguna, id=pk, is_staff=True)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_staff'))
    
    if request.user.is_superuser:
        if user_target.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa aktifkan data Anda sendiri.")
            return redirect (reverse('cbt:user_staff'))

    # Toggle status aktif
    user_target.is_active = not user_target.is_active
    user_target.save()
    if user_target.is_active:
        messages.success(request, "Akun berhasil diaktifkan.")
    else:
        messages.success(request, "Akun berhasil dinonaktifkan.")

    return redirect(reverse("cbt:user_staff"))





login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def user_siswa (request):
    cari = request.POST.get('cari', request.GET.get('cari', '')) 
    items_per_page = request.GET.get('items_per_page', '30')  # Ubah ke string dulu
    
    # Jika memilih "Semua", set items_per_page ke jumlah besar
    if items_per_page == 'all':
        items_per_page = 1000000  # Angka besar untuk menampilkan semua
    else:
        try:
            items_per_page = int(items_per_page)
        except (ValueError, TypeError):
            items_per_page = 30  # Default jika invalid

    data_list = models.Pengguna.objects.filter(
        is_superuser=False, 
        is_siswa=True, Nama_User=request.user
        ).order_by(F('nomor_peserta').asc(nulls_last=True), 'Nama')
    if cari:
        data_list = data_list.filter(Nama__icontains=cari) | data_list.filter(username__icontains=cari)

    paginator = Paginator(data_list, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        Data = paginator.page(page_number)
    except PageNotAnInteger:
        Data = paginator.page(1)
    except EmptyPage:
        Data = paginator.page(paginator.num_pages)

    semua = str(items_per_page) if items_per_page != 1000000 else 'all'
    Data.start_index = (Data.start_index() - 1)
    jumlah = data_list.count()
    
    context = {
        "data": "List Siswa",
        "judul": "CBT-Siswa",
        "Data": Data,
        "jumlah": jumlah,
        "cari": cari,
        "items_per_page": semua ,
        "lembaga": "Akun Siswa",
        "placeholder": "Username/Nama siwa",
        "icon":"bi bi-database-check"
    }
    
    return render (request, 'super_admin/list_user_siswa.html', context)




login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def active_user_siswa(request, pk):
    try:
        pk = int(pk)
    except ValueError:
        messages.error(request, "ID user siswa tidak valid.")
        return redirect(reverse('cbt:user_siswa'))  
    try:
        user_target = get_object_or_404(models.Pengguna, id=pk, is_siswa=True)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_siswa'))
    
    if request.user.is_superuser:
        if user_target.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa aktifkan data Anda sendiri.")
            return redirect (reverse('cbt:user_siswa'))

    # Toggle status aktif
    user_target.is_active = not user_target.is_active
    user_target.save()
    if user_target.is_active:
        messages.success(request, "Akun berhasil diaktifkan.")
    else:
        messages.success(request, "Akun berhasil dinonaktifkan.")

    return redirect(reverse("cbt:user_siswa"))







def get_last_nomor_peserta(lembaga):
    nomor_terakhir = 0
    for nomor in models.Pengguna.objects.filter(
        is_siswa=True, Nama_Lembaga=lembaga
    ).values_list('nomor_peserta', flat=True):
        try:
            nomor_terakhir = max(nomor_terakhir, int(nomor))
        except (TypeError, ValueError):
            continue
    return nomor_terakhir


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_user_siswa(request):
    form = forms.Form_siswa(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            lembaga_aktif = models.Lembaga.objects.filter(status=True).first()
            if not lembaga_aktif:
                messages.error(request, 'Tidak ada lembaga dengan status aktif.')
            else:
                form.instance.nomor_peserta = f"{get_last_nomor_peserta(lembaga_aktif) + 1:05d}"
                form.instance.Nama_User = request.user
                form.instance.Nama_Lembaga = lembaga_aktif
                form.instance.is_siswa = True

                # 🔹 Karakter allowed: hanya huruf kapital + angka, tanpa O, I, 0, 1
                allowed_chars = ''.join([
                    ch for ch in (string.ascii_uppercase + string.digits)
                    if ch not in ['O', 'I', '0', '1']
                ])

                # 🔹 Generate password random huruf besar semua
                auto_password = ''.join(random.choice(allowed_chars) for _ in range(8))

                # 🔹 Simpan password plain untuk ditampilkan
                form.instance.auto_password = auto_password

                # 🔹 Set password Django (hash)
                form.instance.set_password(auto_password)

                # 🔹 Simpan user
                form.save()

                messages.success(
                    request,
                    f"User siswa berhasil dibuat. Username: {form.instance.username}, Password: {auto_password}"
                )
                return redirect(reverse('cbt:user_siswa'))
        else:
            messages.error(request, 'Data Masih Salah.')

    context = {
        "data": "Tambah User Siswa",
        "NamaForm": "Form Tambah User Siswa",
        "judul": "CBT-User Siswa",
        "link": reverse("cbt:user_siswa"),
        "form": form,
        "icon": "bi bi-plus-circle"
    }
    return render(request, 'super_admin/form.html', context)







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def hapus_user_siswa(request):
    
    if request.method == "POST":
        selected_ids = request.POST.getlist('selected_ids')
        if not selected_ids:
            messages.warning(request, 'Tidak ada data yang dipilih untuk dihapus.')
            return redirect(reverse('cbt:user_siswa'))  
        
        Data = models.Pengguna.objects.filter(id__in=selected_ids)
        if not Data.exists():
            raise Http404("Data Madrasah tidak ditemukan.")
        
        if 'confirm' in request.POST:
            Data.delete()  
            messages.success(request, 'Data telah berhasil dihapus.')
            return redirect(reverse('cbt:user_siswa')) 

        messages.warning(request, 'Konfirmasi hapus diperlukan.')
        return redirect(reverse('cbt:user_siswa'))
    
    return redirect(reverse('cbt:user_siswa'))







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_user_siswa(request, pk):
    try:
        pk = int(pk)
    except ValueError:
        messages.error(request, "ID user siswa tidak valid.")
        return redirect(reverse('cbt:user_siswa'))

    try:
        Data = get_object_or_404(models.Pengguna, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_siswa'))
    
    if request.user.is_superuser:
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa ubah data Anda sendiri.")
            return redirect (reverse('cbt:user_siswa'))

    
    
    form = forms.Form_siswa(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, 'Data telah berhasil diubah')
            return redirect(reverse('cbt:user_siswa'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Ubah user Siswa",
        "NamaForm": "Form ubah user Siswa",
        "judul":"CBT-user Siswa",
        "link":reverse("cbt:user_siswa"),
        "form":form,
        "icon":"bi bi-pencil"
        
        }
    return render (request, 'super_admin/form.html', context)



UPLOAD_BATCH_SIZE = 100


def clear_upload_session_data(request):
    keys = [
        'duplicate_users',
        'invalid_usernames',
    ]
    for key in keys:
        request.session.pop(key, None)


def _cell_text(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def read_upload_rows(uploaded_file):
    nama_file = uploaded_file.name.lower()
    if nama_file.endswith('.csv'):
        isi = uploaded_file.read().decode('utf-8-sig').splitlines()
        return [[cell.strip() for cell in row] for row in csv.reader(isi)]
    if nama_file.endswith(('.xlsx', '.xlsm')):
        workbook = load_xlsx(uploaded_file, data_only=True)
        sheet = workbook.active
        return [[_cell_text(cell) for cell in row] for row in sheet.iter_rows(values_only=True)]
    if nama_file.endswith('.xls'):
        workbook = xlrd.open_workbook(file_contents=uploaded_file.read())
        sheet = workbook.sheet_by_index(0)
        return [
            [_cell_text(sheet.cell_value(r, c)) for c in range(sheet.ncols)]
            for r in range(sheet.nrows)
        ]
    raise ValueError("Format file harus CSV, XLS, atau XLSX.")









@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
@transaction.atomic
def uploadUserSiswa(request):
    failed_rows = []
    success_count = 0

    if request.method == "POST":
        form = forms.UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = request.FILES["file"]

            # Validasi format file
            if not upload_file.name.lower().endswith(('.csv', '.xls', '.xlsx', '.xlsm')):
                messages.error(request, "File harus berformat CSV, XLS, atau XLSX.")
                return render(request, "super_admin/upload.html", {
                    "form": form,
                    "failed_rows": failed_rows,
                })

            lembaga_aktif = models.Lembaga.objects.filter(status=True).first()
            if not lembaga_aktif:
                messages.error(request, "Tidak ada lembaga dengan status=True di database.")
                return render(request, "super_admin/upload.html", {
                    "form": form,
                    "failed_rows": failed_rows,
                })

            try:
                rows = read_upload_rows(upload_file)
                if not rows:
                    messages.error(request, "File kosong.")
                    return render(request, "super_admin/upload.html", {
                        "form": form,
                        "failed_rows": failed_rows,
                    })

                header = [cell.strip().lower() for cell in rows[0]]
                # Format: Username, Nama Siswa, Kelas, Rombel
                if len(header) < 4:
                    messages.error(
                        request,
                        "Format header tidak sesuai (minimal 4 kolom: username, nama, kelas, rombel)."
                    )
                    return render(request, "super_admin/upload.html", {
                        "form": form,
                        "failed_rows": failed_rows,
                    })

                kolom_username, kolom_nama, kolom_kelas, kolom_rombel = 0, 1, 2, 3
                minimal_kolom = 4

                # Preload kelas/rombel agar tidak query per baris
                kelas_map = {}
                for obj_kelas in models.Kelas.objects.all():
                    kelas_map.setdefault(obj_kelas.kelas.lower(), obj_kelas)

                rombel_map = {}
                for obj_rombel in models.Rombel_kelas.objects.filter(Nama_Lembaga=lembaga_aktif):
                    if obj_rombel.Rombel:
                        rombel_map.setdefault(obj_rombel.Rombel.lower(), obj_rombel)

                allowed_chars = ''.join([
                    ch for ch in (string.ascii_uppercase + string.digits)
                    if ch not in ['O', 'I', '0', '1']
                ])

                nomor_berikut = get_last_nomor_peserta(lembaga_aktif) + 1
                used_usernames = {
                    uname.lower()
                    for uname in models.Pengguna.objects.values_list('username', flat=True)
                }

                batch = []

                def hash_passwords(passwords):
                    if not passwords:
                        return []
                    workers = min(8, os.cpu_count() or 2, len(passwords))
                    if workers <= 1:
                        return [make_password(pw) for pw in passwords]
                    with ThreadPoolExecutor(max_workers=workers) as pool:
                        return list(pool.map(make_password, passwords))

                def simpan_batch():
                    nonlocal success_count
                    if not batch:
                        return
                    hashed_passwords = hash_passwords(
                        [item['auto_password'] for item in batch]
                    )
                    objects = [
                        models.Pengguna(
                            username=item['username'],
                            password=hashed,
                            Nama_User=request.user,
                            Nama=item['nama'],
                            kelas=item['kelas'],
                            rombel=item['rombel'],
                            Nama_Lembaga=lembaga_aktif,
                            nomor_peserta=item['nomor_peserta'],
                            is_siswa=True,
                            auto_password=item['auto_password'],
                        )
                        for item, hashed in zip(batch, hashed_passwords)
                    ]
                    try:
                        with transaction.atomic():
                            models.Pengguna.objects.bulk_create(
                                objects, batch_size=UPLOAD_BATCH_SIZE
                            )
                        success_count += len(objects)
                    except Exception:
                        # Jika batch gagal, simpan per baris agar data lain tetap masuk
                        for obj, item in zip(objects, batch):
                            try:
                                with transaction.atomic():
                                    obj.save(force_insert=True)
                                success_count += 1
                            except Exception as e:
                                failed_rows.append({
                                    'Nama': item['nama'],
                                    'Kelas': item['kelas_nama'],
                                    'Error': f'Gagal membuat user: {str(e)}'
                                })
                    batch.clear()

                # Proses setiap baris
                for row in rows[1:]:
                    if len(row) < minimal_kolom:
                        failed_rows.append({
                            'Nama': '',
                            'Kelas': '',
                            'Error': 'Format kolom tidak lengkap'
                        })
                        continue

                    username = row[kolom_username].strip()
                    nama = row[kolom_nama].strip()
                    kelas_nama = row[kolom_kelas].strip()
                    rombel_nama = row[kolom_rombel].strip()

                    if not nama:
                        # Lewati baris kosong/baris contoh template yang belum diisi
                        continue

                    if not username:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'Username wajib diisi'
                        })
                        continue
                    if not (username.isascii() and username.isalnum()):
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'Username hanya boleh huruf dan angka'
                        })
                        continue
                    if len(username) > 20:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': f'Username maksimal 20 karakter ({len(username)})'
                        })
                        continue
                    if username.lower() in used_usernames:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': f'Username "{username}" sudah dipakai'
                        })
                        continue

                    # Cek kelas dari data yang sudah di-preload
                    kelas = kelas_map.get(kelas_nama.lower())
                    if not kelas:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'Kelas tidak ditemukan'
                        })
                        continue

                    # Cek rombel dari data yang sudah di-preload
                    rombel_obj = rombel_map.get(rombel_nama.lower())
                    if not rombel_obj:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': f'Rombel "{rombel_nama}" tidak ditemukan'
                        })
                        continue

                    used_usernames.add(username.lower())
                    nomor_peserta = f"{nomor_berikut:05d}"
                    nomor_berikut += 1
                    auto_password = ''.join(random.choice(allowed_chars) for _ in range(8))

                    batch.append({
                        'nama': nama,
                        'kelas_nama': kelas_nama,
                        'kelas': kelas,
                        'rombel': rombel_obj,
                        'username': username,
                        'nomor_peserta': nomor_peserta,
                        'auto_password': auto_password,
                    })

                    if len(batch) >= UPLOAD_BATCH_SIZE:
                        simpan_batch()

                simpan_batch()

                # Pesan hasil
                if failed_rows:
                    messages.warning(
                        request,
                        f"{success_count} berhasil diupload, {len(failed_rows)} gagal. Silakan periksa rincian kesalahan di bawah."
                    )
                else:
                    messages.success(request, f"{success_count} user siswa berhasil diupload!")

            except Exception as e:
                messages.error(request, f"Kesalahan saat memproses file: {str(e)}")

    else:
        form = forms.UploadForm()

    context = {
        "data": "Upload Data Siswa",
        "NamaForm": "Form Upload User Siswa",
        "judul": "PPDB Upload Siswa",
        "link": reverse("cbt:user_siswa"),
        "form": form,
        "download": reverse("cbt:downloadtempUserSiswa"),
        "failed_rows": failed_rows,
        "icon": "bi bi-box-arrow-in-down"
    }
    return render(request, 'super_admin/upload.html', context)











@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def downloadtempUserSiswa(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="template_user_siswa.xls"'

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Data Siswa')

    header_style = xlwt.easyxf('font: bold on; align: horiz center')
    headers = ['Username', 'Nama Siswa', 'Kelas', 'Rombel']
    for kolom, judul in enumerate(headers):
        sheet.write(0, kolom, judul, header_style)

    sheet.col(0).width = 7000
    sheet.col(1).width = 9000
    sheet.col(2).width = 4000
    sheet.col(3).width = 4000

    # Tulis satu baris contoh per kelas
    for baris, kelas in enumerate(models.Kelas.objects.all(), start=1):
        sheet.write(baris, 0, '')
        sheet.write(baris, 1, '')
        sheet.write(baris, 2, kelas.kelas)
        sheet.write(baris, 3, '')

    workbook.save(response)
    return response







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def cetak_semua_kartu_pdf(request):
    user = request.user

    # Ambil semua siswa, sertakan auto_password dan nomor peserta
    semua_siswa = list(
    models.Pengguna.objects.filter(is_siswa=True)
        .order_by('kelas__kelas', 'rombel__Rombel', 'Nama')
        .only('username', 'Nama', 'kelas__kelas', 'rombel__Rombel', 'auto_password', 'nomor_peserta')
    )

    # Ambil data pendukung
    semester = models.SEMESTER.objects.filter(Nama_User=user).last()
    lembaga = models.Lembaga.objects.filter(Nama_User=user).last()
    tahun_pelajaran = models.TahunPelajaran.objects.filter(status=True).last()
    # Ambil jenis ujian aktif
    ujian = models.Jenis_Ujian.objects.filter(Nama_User=user,status=True).last()

    

    # Potong 10 kartu per halaman
    def chunk_siswa(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]
    pages = list(chunk_siswa(semua_siswa, 10))

    # Ambil logo
    static_dir = settings.STATIC_ROOT or settings.STATICFILES_DIRS[0]
    logo_path = os.path.join(static_dir, 'logo/img/KEMENAG.png')
    logo_url = f'file://{logo_path}'

    # Kirim auto_password ke template bersama siswa
    context = {
        'pages': pages,  # setiap siswa di pages punya .auto_password
        'semester': semester,
        'lembaga': lembaga,
        'tahun_pelajaran': tahun_pelajaran,
        'logo_kemenag': logo_url,
        'ujian': ujian,
    }

    # Render HTML ke PDF
    html_string = render_to_string("super_admin/kartu_ujian.html", context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Kartu_ujian.pdf"'
    html.write_pdf(response)

    return response



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_staff, login_url=settings.LOGIN_URL)
@csrf_protect
def generate_ulang_password_per_siswa(request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID tidak valid.")
        return redirect('cbt:user_siswa')
    try:
        siswa = get_object_or_404(models.Pengguna, id=pk)
    except Http404 :
        messages.error(request,'Siswa tidak ditemukan atau bukan siswa Anda.')
        return redirect('cbt:user_siswa')
    context =   {
        'judul':"Generet password siswa",
        'data':"Generet password siswa",
        'siswa': siswa,
        "link": reverse('cbt:user_siswa'),
        "icon":"bi bi-arrow-repeat"
    }
    return render(request,'super_admin/generate_password_per_siswa.html', context)





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_staff, login_url=settings.LOGIN_URL)
@csrf_protect
def generate_password_persiswa(request, pk):
    try:
        pk= int(pk)
    except ValueError:
        messages.error(request, "ID tidak valid.")
        return redirect('cbt:user_siswa')
    if request.method == 'POST':
        try:
            siswa = get_object_or_404(models.Pengguna, id=pk,)
        except models.Pengguna.DoesNotExist:
            messages.error(request,'Siswa tidak ditemukan atau bukan siswa Anda.')
            return redirect('cbt:user_siswa')

        # Karakter yang diperbolehkan
        allowed_chars = ''.join([
            ch for ch in (string.ascii_uppercase + string.digits)
            if ch not in ['O', 'I', '0', '1']
        ])

        # Generate password tepat 8 karakter
        auto_password = ''.join(
            random.choice(allowed_chars)
            for _ in range(8)
        )

        # Hash password Django
        siswa.set_password(auto_password)

        # Simpan password asli
        siswa.auto_password = auto_password

        # Simpan
        siswa.save(update_fields=[
            'password',
            'auto_password',
        ])

        messages.success(
            request,
            f'Berhasil generate password siswa {siswa.Nama}.'
        )

        return redirect('cbt:user_siswa')

    return redirect('cbt:user_siswa')





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_staff, login_url=settings.LOGIN_URL)
def generate_ulang_password_siswa(request):

    siswa_count = models.Pengguna.objects.filter(is_siswa=True,Nama_User=request.user).count()
    context =   {
        'judul':"Generet password siswa",
        'data':"Generet password siswa",
        'siswa_count': siswa_count,
        'generet': reverse ('cbt:proses_generate_password_siswa'),
        "link": reverse('cbt:user_siswa'),
        "icon":"bi bi-arrow-repeat"
    }
    return render(request,'super_admin/generate_ulang_password_siswa.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_staff, login_url=settings.LOGIN_URL)
@csrf_protect
def proses_generate_password_siswa(request):

    if request.method == 'POST':

        # Karakter yang diperbolehkan
        allowed_chars = ''.join([
            ch for ch in (string.ascii_uppercase + string.digits)
            if ch not in ['O', 'I', '0', '1']
        ])

        # Hanya siswa dari lembaga user yang sedang login
        siswa_list = models.Pengguna.objects.filter(
            is_siswa=True,
            Nama_User=request.user,
        )

        jumlah = 0

        for siswa in siswa_list:

            # Generate password tepat 8 karakter
            auto_password = ''.join(
                random.choice(allowed_chars)
                for _ in range(8)
            )

            # Password di-hash oleh Django
            siswa.set_password(auto_password)

            # Simpan password asli untuk ditampilkan/admin
            siswa.auto_password = auto_password

            siswa.save(update_fields=[
                'password',
                'auto_password',
            ])

            jumlah += 1

        messages.success(
            request,
            f'Berhasil generate ulang password {jumlah} siswa.'
        )

        return redirect(reverse('cbt:user_siswa'))

    return redirect(reverse('cbt:user_siswa'))







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def backup_database(request):
    if request.method == 'POST':
        form = forms.FormDownload(request.POST)

        if form.is_valid():
            user = authenticate(
                username=request.user.username,
                password=form.cleaned_data['password']
            )

            if user and user.is_superuser:
                filename = f"backup_cbt_{now().date()}.json"

                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
                        file_path = temp_file.name

                    # Dump SELURUH DATABASE
                    with open(file_path, 'w') as output_file:
                        call_command(
                            'dumpdata',
                            '--natural-primary',
                            '--natural-foreign',
                            '--indent', '2',
                            stdout=output_file
                        )

                    # Download langsung JSON
                    return FileResponse(
                        open(file_path, 'rb'),
                        as_attachment=True,
                        filename=filename
                    )

                except Exception as e:
                    messages.error(request, f"Gagal backup database: {str(e)}")

                finally:
                    if file_path:
                        cleanup_files(file_path)

            else:
                messages.error(request, "Password salah !!!!!")

    else:
        form = forms.FormDownload()

    context = {
        "judul": "Backup Database",
        "NamaForm": "Form Backup Database",
        "link": reverse('cbt:backup_database'),
        "form": form,
    }
    return render(request, 'super_admin/backup_database.html', context)

















