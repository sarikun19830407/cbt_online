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
from django.http import HttpResponse, Http404
import time 
from django.db.models import Count, Case, When, IntegerField
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static
from django.utils import timezone
from django.db.models import Q


@csrf_protect
@never_cache
def app_cbt (request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect (reverse ("cbt:home"))
        elif user is not None and user.is_staff:
            login(request, user)
            return redirect (reverse ("cbt:staff"))
        elif user is not None and user.is_siswa:
            login(request, user)
            return redirect(reverse('cbt:siswa'))
        elif user is not None :
            login(request, user)
            return redirect('/DasboardSuperuser')
        
        else:
            messages.error(request, 'Gagal Login Username atau Password salah')
            return redirect ("/")
    contex={
        "data":"CBT",
        "judul":"CBT"
    }
    return render (request, 'login.html', contex)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def home (request):
    Data = models.TahunPelajaran.objects.filter(status=True, Nama_User=request.user)
    Siswa = models.Pengguna.objects.filter(is_siswa=True, Nama_User=request.user, Nama_Lembaga = request.user.Nama_Lembaga)
    rombel = models.Rombel_kelas.objects.filter(Nama_User=request.user, Nama_Lembaga = request.user.Nama_Lembaga)
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
def update_userlogin(request):
    form = forms.FormUpdateSuperAdmin(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
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
    Data = models.KurikulumLembaga.objects.all()

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
        Data = get_object_or_404(models.KurikulumLembaga, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:kurikulum_lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:kurikulum_lembaga'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, f'{Data} telah berhasil di hapus')
        return redirect (reverse('cbt:kurikulum_lembaga'))
    context = {
        "data" : "Hapus Kurikulum",
        "judul":"CBT-Kurikulum",
        "link":reverse("cbt:kurikulum_lembaga"),
        "Data":f"Mapel {Data}",
        'icon':"bi bi-trash3"
        }
    return render (request, 'super_admin/hapus.html', context)





@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_kurikulum (request, pk):
    try:
        Data = get_object_or_404(models.KurikulumLembaga, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:kurikulum_lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:kurikulum_lembaga'))
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
    Data = models.TahunPelajaran.objects.all()
    context ={
        "data":"Tahun Pelajaran",
        "judul":"CBT-Tahun Pelabi bi-plus-circlejaran",
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
        Data = get_object_or_404(models.TahunPelajaran, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:tahun_pelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:tahun_pelajaran'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:tahun_pelajaran'))
    context = {
        "data" : f"Hapus Tahun Pelajaran {Data}",
        "judul":"CBT",
        "link":reverse("cbt:tahun_pelajaran"),
        "Data":f"tahun pelajaran {Data}",
        "icon":"bi bi-trash3"
        }
    return render (request, 'super_admin/hapus.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_Tahun_Pelajaran (request, pk):
    try:
        Data = get_object_or_404(models.TahunPelajaran, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:tahun_pelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:tahun_pelajaran'))
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
        Data = get_object_or_404(models.Lembaga, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:lembaga'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, f'{Data} telah berhasil di hapus')
        return redirect (reverse('cbt:lembaga'))
    context = {
        "data" : f"Hapus lembaga {Data}",
        "judul":"CBT-Lembaga",
        "link":reverse("cbt:lembaga"),
        "Data":f"lembaga {Data}",
        'icon':"bi bi-trash3"
        }
    return render (request, 'super_admin/hapus.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_lembaga (request, pk):
    try:
        Data = get_object_or_404(models.Lembaga, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:lembaga'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:lembaga'))
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
def Kelas(request):
    Data = models.Kelas.objects.all()
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
            form.instance.Nama_User = request.user
            lembaga_aktif = get_object_or_404(models.Lembaga, status=True)
            form.instance.Nama_Lembaga = lembaga_aktif
            form.instance.satatus = True
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:Kelas'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Tambah Kelas",
        "NamaForm": "Form Tambah Kelas",
        "judul":"CBT-Kelas",
        "link":reverse("cbt:Kelas"),
        "form":form,
        "icon":"bi bi-plus-circle"
        }
    return render (request, 'super_admin/form.html', context)


@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def hapus_kelas (request, pk):
    try:
        Data = get_object_or_404(models.Kelas, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:Kelas'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:Kelas'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:Kelas'))
    context = {
        "data" : f"Hapus Kelas {Data}",
        "judul":"CBT-Kelas",
        "link":reverse("cbt:Kelas"),
        "Data":f'kelas {Data}',
        "icon":"bi bi-trash3"
        }
    return render (request, 'super_admin/hapus.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_Kelas (request, pk):
    try:
        Data = get_object_or_404(models.Kelas, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:Kelas'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:Kelas'))
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
    Data = models.Rombel_kelas.objects.all()
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
            lembaga_aktif = get_object_or_404(models.Lembaga, status=True)
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
        Data = get_object_or_404(models.Rombel_kelas, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:Rombel'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:Rombel'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:Rombel'))
    context = {
        "data" : f"Hapus Rombel {Data}",
        "judul":"CBT-Rombel",
        "link":reverse("cbt:Rombel"),
        "Data":f'Rombel {Data}',
        "icon":"bi bi-trash3"
        }
    return render (request, 'super_admin/hapus.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def ubah_rombel (request, pk):
    try:
        Data = get_object_or_404(models.Rombel_kelas, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:Rombel'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:Rombel'))
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
            lembaga_aktif = get_object_or_404(models.Lembaga, status=True)
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
        Data = get_object_or_404(models.Matapelajaran, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:matapelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:matapelajaran'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:matapelajaran'))
    context = {
        "data" : "Hapus Mata Peklajaran",
        "judul":"CBT-Mapel",
        "link":reverse("cbt:matapelajaran"),
        "Data":f"Mapel {Data}",
        'icon':"bi bi-trash3"
        }
    return render (request, 'super_admin/hapus.html', context)




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_Mata_Pelajaran (request, pk):
    try:
        Data = get_object_or_404(models.Matapelajaran, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:matapelajaran'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:matapelajaran'))
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

    data_list = models.Pengguna.objects.filter(is_staff=True, is_superuser=False)
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
            messages.add_message(request, messages.INFO, 'Data telah berhasil Tambahkan')
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
        Data = get_object_or_404(models.Pengguna, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_staff'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:user_staff'))

    if request.method == "POST":
        Data.delete()
        messages.add_message(request, messages.INFO, 'Data telah berhasil Hapus')
        return redirect (reverse('cbt:user_staff'))
    context = {
        "data" : f"Hapus {Data}",
        "judul":"CBT-user staff",
        "link":reverse("cbt:user_staff"),
        "Data":Data,
        "icon":"bi bi-trash"
        }
    return render (request, 'super_admin/hapus.html', context)



@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_user_staff (request, pk):
    
    try:
        Data = get_object_or_404(models.Pengguna, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_staff'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:user_staff'))
    form = forms.Form_Ubah_Staff(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil diubah')
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
    user_target = get_object_or_404(models.Pengguna, id=pk, is_staff=True)

    # Toggle status aktif
    user_target.is_active = not user_target.is_active
    user_target.save()

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
        is_siswa=True
        ).order_by('Kelas__Kelas', 'Rombel__Rombel',"Nama")
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
    user_target = get_object_or_404(models.Pengguna, id=pk, is_siswa=True)

    # Toggle status aktif
    user_target.is_active = not user_target.is_active
    user_target.save()

    return redirect(reverse("cbt:user_siswa"))




@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def tambah_user_siswa(request):
    form = forms.Form_siswa(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.instance.Nama_User = request.user
            lembaga_aktif = get_object_or_404(models.Lembaga, status=True)
            form.instance.Nama_Lembaga = lembaga_aktif
            form.instance.is_siswa = True
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil Tambahkan')
            return redirect(reverse('cbt:user_siswa'))
        else:
            messages.error(request, 'Data Masih Salah.')
    context = {
        "data" : "Tambah User Siswa",
        "NamaForm": "Form Tambah User Siswa",
        "judul":"CBT-User Siswa",
        "link":reverse("cbt:user_siswa"),
        "form":form,
        "icon":"bi bi-plus-circle"
        
        }
    return render (request, 'super_admin/form_user.html', context)





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
        
        # Pemeriksaan kepemilikan data
        for data in Data:
            if data.Nama_User != request.user:
                messages.error(request, "Anda tidak memiliki hak akses untuk menghapus data ini.")
                return redirect(reverse('cbt:user_siswa'))
        
        if 'confirm' in request.POST:
            Data.delete()  
            messages.success(request, 'Data telah berhasil dihapus.')
            return redirect(reverse('cbt:user_siswa')) 
        
        context = {
            "data" : f"Hapus {Data.count()} siswa",
            "NamaForm": "Form Hapus Madrsah",
            "judul":"PPDB Hapus Madrsah",
            "link":reverse("cbt:user_siswa"),
            "hapus": reverse('cbt:hapus_user_siswa'),
            "Data": Data,
            "Hapus":f"{Data.count()} siswa",
            "ket":"Madrasah",
            "icon":"bi bi-trash3"
        }
        return render(request, 'super_admin/hapu_data.html', context)
    
    return redirect(reverse('cbt:user_siswa'))







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def Ubah_user_siswa(request, pk):
    try:
        Data = get_object_or_404(models.Pengguna, id=pk)
    except Http404:
        messages.error(request, "Data pengguna tidak ditemukan.")
        return redirect(reverse('cbt:user_siswa'))  # Redirect ke halaman daftar pengguna
    
    if request.user.is_superuser:
        # Pengguna provinsi hanya bisa mengedit dirinya sendiri
        if Data.Nama_User != request.user:
            messages.error(request, "Anda hanya bisa mengedit data Anda sendiri.")
            return redirect(reverse('cbt:user_siswa'))
    form = forms.Form_Ubah_siswa(request.POST or None, instance=Data)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Data telah berhasil diubah')
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
    return render (request, 'super_admin/form_user.html', context)



def clear_upload_session_data(request):
    keys = [
        'duplicate_users',
        'invalid_usernames',
    ]
    for key in keys:
        request.session.pop(key, None)








@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
@transaction.atomic
def uploadUserSiswa(request):
    failed_rows = []
    success_count = 0
    processed_usernames = set()

    if request.method == "POST":
        form = forms.UploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["file"]

            # Validasi format file
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "File harus dalam format CSV.")
                return render(request, "super_admin/upload.html", {
                    "form": form,
                    "failed_rows": failed_rows,
                })

            # Ambil lembaga aktif sekali saja
            lembaga_aktif = models.Lembaga.objects.filter(status=True).first()
            if not lembaga_aktif:
                messages.error(request, "Tidak ada lembaga dengan status=True di database.")
                return render(request, "super_admin/upload.html", {
                    "form": form,
                    "failed_rows": failed_rows,
                })

            try:
                decoded_file = csv_file.read().decode("utf-8").splitlines()
                reader = csv.reader(decoded_file)

                # Cek apakah file punya header
                try:
                    header = next(reader)
                    if len(header) < 5:
                        messages.error(request, "Format header CSV tidak sesuai (minimal 5 kolom).")
                        return render(request, "super_admin/upload.html", {
                            "form": form,
                            "failed_rows": failed_rows,
                        })
                except StopIteration:
                    messages.error(request, "File CSV kosong.")
                    return render(request, "super_admin/upload.html", {
                        "form": form,
                        "failed_rows": failed_rows,
                    })

                # Proses setiap baris CSV
                for row in reader:
                    if len(row) < 5:
                        failed_rows.append({
                            'Nama': '',
                            'Kelas': '',
                            'Error': 'Format kolom tidak lengkap'
                        })
                        continue

                    username = row[0].strip()
                    password = row[1].strip()
                    nama = row[2].strip()
                    kelas_nama = row[3].strip()
                    rombel_nama = row[4].strip()

                    # Validasi username
                    if not (username.isdigit() and len(username) == 16):
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'NIK harus 16 digit angka'
                        })
                        continue

                    # Cek duplikat di CSV
                    if username in processed_usernames:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'Username ganda dalam file'
                        })
                        continue
                    processed_usernames.add(username)

                    # Cek duplikat di database
                    if models.Pengguna.objects.filter(username__iexact=username).exists():
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'Username sudah ada di database'
                        })
                        continue

                    # Cek kelas
                    kelas = models.Kelas.objects.filter(Kelas__iexact=kelas_nama).first()
                    if not kelas:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': 'Kelas tidak ditemukan'
                        })
                        continue

                    # Cek rombel
                    rombel_obj = models.Rombel_kelas.objects.filter(
                        Q(Kelas=kelas),
                        Q(Rombel__iexact=rombel_nama),
                        Q(Nama_Lembaga=lembaga_aktif)
                    ).first()

                    if not rombel_obj:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': f'Rombel "{rombel_nama}" tidak ditemukan untuk kelas "{kelas_nama}"'
                        })
                        continue

                    # Buat user baru
                    try:
                        models.Pengguna.objects.create_user(
                            username=username,
                            password=password,
                            Nama_User=request.user,
                            Nama=nama,
                            Kelas=kelas,
                            Rombel=rombel_obj,
                            Nama_Lembaga=lembaga_aktif,
                            is_siswa=True,
                        )
                        success_count += 1
                    except Exception as e:
                        failed_rows.append({
                            'Nama': nama,
                            'Kelas': kelas_nama,
                            'Error': f'Gagal membuat user: {str(e)}'
                        })

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
        "data": "Upload User Siswa",
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
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template_user_siswa.csv"'

    writer = csv.writer(response)

    # Header kolom
    writer.writerow(['NIK', 'Password', 'Nama Siswa', 'Kelas', 'Rombel'])

    # Ambil semua Rombel_kelas
    rombel_list = models.Rombel_kelas.objects.select_related('Kelas').all().order_by('Kelas__Kelas', 'Rombel')

    # Tulis satu baris contoh per rombel
    for rombel in rombel_list:
        kelas_nama = rombel.Kelas.Kelas
        rombel_nama = rombel.Rombel
        writer.writerow(['', '', '', kelas_nama, rombel_nama])  # Kosongkan NIK, Password, Nama

    return response







@login_required(login_url=settings.LOGIN_URL)
@user_passes_test(lambda user: user.is_superuser, login_url=settings.LOGIN_URL)
@csrf_protect
def cetak_semua_kartu_pdf(request):
    user = request.user

    # Ambil semua siswa dan urutkan sesuai kebutuhan
    semua_siswa = list(models.Pengguna.objects.filter(is_siswa=True).order_by(
        'Kelas__Kelas', 'Rombel__Rombel', 'Nama'
    ))

    # Tambahkan nomor peserta: mulai dari 0001 dan seterusnya
    for i, siswa in enumerate(semua_siswa, start=1):
        siswa.nomor_peserta = f"{i:04d}"  # 4 digit angka, misalnya 0001, 0002, dst

    # Ambil data pendukung
    semester = models.SEMESTER.objects.filter(Nama_User=user).last()
    lembaga = models.Lembaga.objects.filter(Nama_User=user).last()
    tahun_pelajaran = models.TahunPelajaran.objects.filter(status=True).last()
    tanggal_cetak = timezone.now()

    # Potong 10 kartu per halaman
    def chunk_siswa(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]
    pages = list(chunk_siswa(semua_siswa, 10))

    # # Ambil static dir dari STATICFILES_DIRS
    # static_dir = settings.STATICFILES_DIRS[0]  # karena STATIC_ROOT belum digunakan di dev

    # # Gabungkan path file logo
    # logo_path = os.path.join(static_dir, 'logo/img/KEMENAG.png')

    # # Pastikan file benar-benar ada
    # if not os.path.exists(logo_path):
    #     raise Exception(f"Logo tidak ditemukan di path: {logo_path}")

    # # Buat URL file:// agar bisa dibaca WeasyPrint
    # logo_url = f'file://{logo_path}'

    # Ambil static dir (STATIC_ROOT jika dikompilasi, atau STATICFILES_DIRS di dev)
    static_dir = settings.STATIC_ROOT or settings.STATICFILES_DIRS[0]
    logo_path = os.path.join(static_dir, 'logo/img/KEMENAG.png')
    logo_url = f'file://{logo_path}'

    # Siapkan context untuk template
    context = {
        'pages': pages,
        'semester': semester,
        'lembaga': lembaga,
        'tahun_pelajaran': tahun_pelajaran,
        'tanggal_cetak': tanggal_cetak,
        'logo_kemenag': logo_url,
    }

    # Render HTML ke PDF menggunakan WeasyPrint
    html_string = render_to_string("super_admin/kartu_ujian.html", context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))

    # Siapkan response PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Kartu_ujian.pdf"'
    html.write_pdf(response)

    return response


















