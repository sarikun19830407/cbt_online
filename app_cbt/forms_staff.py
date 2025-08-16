from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from ckeditor.widgets import CKEditorWidget
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from app_cbt import models
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ckeditor.widgets import CKEditorWidget
from bs4 import BeautifulSoup
from django.utils.html import strip_tags
from django.conf import settings




class SetingSoalForm(forms.ModelForm):
    class Meta:
        model = models.SetingSoal
        fields = ['Kelas','Mapel','durasi_menit']

        labels = {
            'durasi_menit': 'Durasi Ujian (dalam menit)',
        }

        widgets = {
            "Tahun_Pelajaran": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Semester": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Kelas": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Mapel": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            'durasi_menit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan durasi dalam menit'
            }),
        }




class SoalSiswaForm(forms.ModelForm):
    Soal=forms.CharField(widget=CKEditorWidget(config_name='default'))
    A=forms.CharField(widget=CKEditorWidget(config_name='default'))
    B=forms.CharField(widget=CKEditorWidget(config_name='default'))
    C=forms.CharField(widget=CKEditorWidget(config_name='default'))
    D=forms.CharField(widget=CKEditorWidget(config_name='default'))
    class Meta:
        model = models.Soal_Siswa
        exclude = ['Nama_User', 'Kode_Soal', 'Kelas',"Mapel","Nomor"]


        widgets = {
            "Nomor": forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    
                }
            ),
            "Kunci_Jawaban": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Nilai": forms.NumberInput(
                attrs = {
                    'class':'form-control  mb-3',
                    
                }
            ),
            'Soal': CKEditorWidget(),
            'A': CKEditorWidget(),
            'B': CKEditorWidget(),
            'C': CKEditorWidget(),
            'D': CKEditorWidget(),
            
        }
    
    
class Daftar_nilai(forms.ModelForm):
    class Meta:
        model = models.DaftarNilai
        fields = ['Kelas','Rombel','Mapel',]

        widgets = {
            "Rombel": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Semester": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Kelas": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Mapel": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
        }
    



class UploadForm(forms.Form):
    file = forms.FileField(
        label="file_excel",
        widget=forms.FileInput(attrs={'class': 'form-control mt-2'}),
        required=True
    )