from django.urls import path
from django.contrib.auth.decorators import login_required
from app_cbt.view import view_admin, view_staff, view_siswa
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView


app_name = "cbt"

urlpatterns =[

    path('home', view_admin.home, name='home'),
    path('bersihkan_file_temp', view_admin.bersihkan_file_temp, name='bersihkan_file_temp'),
    path('update_userlogin', view_admin.update_userlogin, name='update_userlogin'),
    path('update_userlogin_Sataff', view_staff.update_userlogin_Sataff, name='update_userlogin_Sataff'),
    path('user_staff', view_admin.user_staff, name='user_staff'),
    path('tambah_user_staff', view_admin.tambah_user_staff, name='tambah_user_staff'),
    path('hapus_user_staff/<pk>/', view_admin.hapus_user_staff, name='hapus_user_staff'),
    path('Ubah_user_staff/<pk>/', view_admin.Ubah_user_staff, name='Ubah_user_staff'),
    path('active_user_staff/<pk>/', view_admin.active_user_staff, name='active_user_staff'),
    
    
    path('user_siswa', view_admin.user_siswa, name='user_siswa'),
    path('tambah_user_siswa', view_admin.tambah_user_siswa, name='tambah_user_siswa'),
    path('active_user_siswa/<pk>/', view_admin.active_user_siswa, name='active_user_siswa'),
    path('hapus_user_siswa', view_admin.hapus_user_siswa, name='hapus_user_siswa'),
    path('Ubah_user_siswa/<pk>/', view_admin.Ubah_user_siswa, name='Ubah_user_siswa'),
    path('uploadUserSiswa', view_admin.uploadUserSiswa, name='uploadUserSiswa'),
    path('downloadtempUserSiswa', view_admin.downloadtempUserSiswa, name='downloadtempUserSiswa'),
    path('cetak_semua_kartu_pdf', view_admin.cetak_semua_kartu_pdf, name='cetak_semua_kartu_pdf'),


    path('lembaga', view_admin.lembaga, name='lembaga'),
    path('tambah_lembaga', view_admin.tambah_lembaga, name='tambah_lembaga'),
    path('Hapus_lembaga/<pk>/', view_admin.Hapus_lembaga, name='Hapus_lembaga'),
    path('Ubah_lembaga/<pk>/', view_admin.Ubah_lembaga, name='Ubah_lembaga'),

    path('kurikulum_lembaga', view_admin.kurikulum_lembaga, name='kurikulum_lembaga'),
    path('tambah_kurikulum', view_admin.tambah_kurikulum, name='tambah_kurikulum'),
    path('Hapus_kurikulum/<pk>/', view_admin.Hapus_kurikulum, name='Hapus_kurikulum'),
    path('Ubah_kurikulum/<pk>/', view_admin.Ubah_kurikulum, name='Ubah_kurikulum'),



    path('Hapus_mapel/<pk>/', view_admin. Hapus_mapel, name=' Hapus_mapel'),
    path('Ubah_Mata_Pelajaran/<pk>/', view_admin.Ubah_Mata_Pelajaran, name='Ubah_Mata_Pelajaran'),

    path('matapelajaran', view_admin.matapelajaran, name='matapelajaran'),
    path('tambah_pelajaran', view_admin.tambah_pelajaran, name='tambah_pelajaran'),

    path('tahun_pelajaran', view_admin.tahun_pelajaran, name='tahun_pelajaran'),
    path('tambah_tahun_pelajaran', view_admin.tambah_tahun_pelajaran, name='tambah_tahun_pelajaran'),
    path('Ubah_Tahun_Pelajaran/<pk>/', view_admin.Ubah_Tahun_Pelajaran, name='Ubah_Tahun_Pelajaran'),
    path('Hapus_Tahun_Pelajaran/<pk>/', view_admin.Hapus_Tahun_Pelajaran, name='Hapus_Tahun_Pelajaran'),
    

    path('semester', view_admin.semester, name='semester'),
    path('Kelas', view_admin.Kelas, name='Kelas'),
    path('tambah_kelas', view_admin.tambah_kelas, name='tambah_kelas'),
    path('hapus_kelas/<pk>/', view_admin.hapus_kelas, name='hapus_kelas'),
    path('Ubah_Kelas/<pk>/', view_admin.Ubah_Kelas, name='Ubah_Kelas'),



    path('Rombel', view_admin.Rombel, name='Rombel'),
    path('tambah_rombel', view_admin.tambah_rombel, name='tambah_rombel'),
    path('hapus_rombel/<pk>/', view_admin.hapus_rombel, name='hapus_rombel'),
    path('ubah_rombel/<pk>/', view_admin.ubah_rombel, name='ubah_rombel'),


    path('backup_database', view_admin.backup_database, name='backup_database'),
    path('restore_database', view_admin.restore_database, name='restore_database'),



# ...................................................................................................................................
# view staf

    path('staff', view_staff.staff, name='staff'),
    path('setting_soal', view_staff.setting_soal, name='setting_soal'),

    path('setting_soal', view_staff.setting_soal, name='setting_soal'),
    path('buat_seting_soal', view_staff.buat_seting_soal, name='buat_seting_soal'),
    path('hapus_setting_soal', view_staff.hapus_setting_soal, name='hapus_setting_soal'),
    path('Ubah_setting_soal/<pk>/', view_staff.Ubah_setting_soal, name='Ubah_setting_soal'),


    path('buat_soal_siswa/<pk>/', view_staff.buat_soal_siswa, name='buat_soal_siswa'),
    path('hapus_soal/<int:pk>/', view_staff.hapus_soal, name='hapus_soal'),
    path('Ubah_soal/<int:pk>/', view_staff.Ubah_soal, name='Ubah_soal'),
    path('upload_soal_excel/<pk>/', view_staff.upload_soal_excel, name='upload_soal_excel'),
    path('download_template_soal', view_staff.download_template_soal, name='download_template_soal'),
    path('lihat_soal_siswa/<pk>/', view_staff.lihat_soal_siswa, name='lihat_soal_siswa'),
    path('hapus_soal_pilih', view_staff.hapus_soal_pilih, name='hapus_soal_pilih'),

    path('ujicoba_soal/<int:pk>/', view_staff.ujicoba_soal, name='ujicoba_soal'),
    path('ujicoba_selesai/<int:pk>/ujicoba_selesai/', view_staff.ujicoba_selesai, name='ujicoba_selesai'),

    path('nilai_setingsoal/<str:kode_soal>/', view_staff.nilai_setingsoal, name='nilai_setingsoal'),
    path('nilai/<str:kode_soal>/download/', view_staff.export_nilai_excel_setting, name='export_nilai_excel_setting'),
    path('aktifkan-soal/<str:kode_soal>/', view_staff.aktifkan_soal, name='aktifkan_soal'),




    
    path('daftar_nilai', view_staff.daftar_nilai, name='daftar_nilai'),
    path('tambah_daftar_nilai', view_staff.tambah_daftar_nilai, name='tambah_daftar_nilai'),
    path('jawaban_siswa/<int:id_daftarnilai>/', view_staff.jawaban_siswa, name='jawaban_siswa'),
    path('daftar_nilai_view/<int:id_daftarnilai>/', view_staff.daftar_nilai_view, name='daftar_nilai_view'),
    path('ubah_daftar_nilai/<pk>/', view_staff.ubah_daftar_nilai, name='ubah_daftar_nilai'),
    path('hapus_daftar_nilai', view_staff.hapus_daftar_nilai, name='hapus_daftar_nilai'),
    path('xport_jawaban_siswa_excel/<int:id_daftarnilai>/', view_staff.export_jawaban_siswa_excel, name='export_jawaban_siswa'),
    path('export_daftar_nilai_excel/<int:id_daftarnilai>/', view_staff.export_daftar_nilai_excel, name='export_daftar_nilai'),
    path('export_daftar_nilai_pdf/<int:id_daftarnilai>/', view_staff.export_daftar_nilai_pdf, name='export_daftar_nilai_pdf'),
    path('export_jawaban_siswa_pdf/<int:id_daftarnilai>/', view_staff.export_jawaban_siswa_pdf, name='export_jawaban_siswa_pdf'),


    path('reset_login', view_staff.reset_login, name='reset_login'),


    path('arsip_soal', view_staff.arsip_soal, name='arsip_soal'),
    path('setting_soal_arsip/<int:pk>/', view_staff.setting_soal_arsip, name='setting_soal_arsip'),
    path('salin_setingsoal/<int:pk>/', view_staff.salin_setingsoal, name='salin_setingsoal'),
    path('lihat_arsip_soal_siswa/<pk>/', view_staff.lihat_arsip_soal_siswa, name='lihat_arsip_soal_siswa'),
    path('arsip_daftar_nilai/<int:pk>/', view_staff.arsip_daftar_nilai, name='arsip_daftar_nilai'),
    path('hapus_arsip_daftar_nilai', view_staff.hapus_arsip_daftar_nilai, name='hapus_arsip_daftar_nilai'),
    path('arsip_jawaban_siswa/<int:pk>/', view_staff.arsip_jawaban_siswa, name='arsip_jawaban_siswa'),
    path('arsip_daftar_nilai_view/<int:pk>/', view_staff.arsip_daftar_nilai_view, name='arsip_daftar_nilai_view'),




    # ...................................................................................................................................
# view siswa

    path('siswa', view_siswa.siswa, name='siswa'),
    path('mulai_ujian/<kode_soal>/', view_siswa.mulai_ujian, name='mulai_ujian'),
    path('selesai_ujian/<str:kode_soal>/selesai_ujian/', view_siswa.selesai_ujian, name='selesai_ujian'),
    
    # urls.py
    



    path('Logaut', LogoutView.as_view(next_page='/'), name='Logaut'),
    path('<path:unused>', RedirectView.as_view(url='/', permanent=False)),
    path('', view_admin.app_cbt, name='app_cbt'),
]