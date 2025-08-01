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




class FormUpdateSuperAdmin (ModelForm):
    password1 = forms.CharField(
        label= ("Masukan Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password1"
        }),
        
    )
    password2 = forms.CharField(
        label= ("Konfirmaasi Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password2"
        }),
        
    )
    class Meta : 
        model = models.Pengguna
        fields = [
            "username",
            "Nama",
            "Tikatan_Satuan_Lembaga",
            "Nama_Lembaga",
            "password1",
            "password2",
            

        ]

        help_texts = {
            'username': None,
            # 'email': None,
        }

        labels={
            
        }
        widgets = {
            "username": forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    'placeholder':"NISN Terdiri 10 digit",
                }
            ),
            "Nama": forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    'placeholder':"Nama Anda",
                }
            ),
            "Nama_Lembaga": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    'placeholder':"Nama Anda",
                }
            ),
            "Tikatan_Satuan_Lembaga": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    'placeholder':"Nama Anda",
                }
            ),
            
            
        }

        def clean(self):
            cleaned_data = super().clean()
            password1 = cleaned_data.get('password1')
            password2 = cleaned_data.get('password2')

            # Validasi: Jika salah satu password diisi, kedua field harus sama
            if password1 or password2:
                if password1 != password2:
                    raise forms.ValidationError("")
            
            return cleaned_data

        def save(self, commit=True):
            user = super().save(commit=False)
            password = self.cleaned_data.get('password1')

            # Jika password diisi, set password baru
            if password:
                user.set_password(password)

            if commit:
                user.save()

            return user
        
        def clean_password1(self):
            password = self.cleaned_data.get('password1')
            
            # Check minimum length
            if len(password) < 8:
                raise ValidationError("Password harus memiliki minimal 8 karakter.")
            
            # Check for at least one uppercase letter
            if not any(char.isupper() for char in password):
                raise ValidationError("Password harus memiliki minimal 1 huruf kapital.")
            
            # Check for at least one digit
            if not any(char.isdigit() for char in password):
                raise ValidationError("Password harus memiliki minimal 1 angka.")
            return password
            
        def __init__(self, *args, **kwargs):
            super(FormUpdateSuperAdmin, self).__init__(*args, **kwargs)
            del self.fields['Nama']










class FormTahunPeljaran(forms.ModelForm):
    class Meta:
        model = models.TahunPelajaran
        fields = ['Tahun_Pelajaran', 'tanggal_penetapan']
        widgets = {
            'Tahun_Pelajaran': forms.Select(attrs={'class': 'form-select mb-3'}),
            'tanggal_penetapan': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super(FormTahunPeljaran, self).__init__(*args, **kwargs)
        
        # Tentukan tahun ajaran aktif berdasarkan bulan berjalan
        now = datetime.now()
        if now.month >= 7:
            tahun_awal = now.year
        else:
            tahun_awal = now.year - 1

        # Dropdown pilihan tahun ajaran, misal dari 2024/2025 hingga 2030/2031
        start_year = 2024
        end_year = tahun_awal + 5
        start_year = tahun_awal - 2  # misalnya tampilkan 2 tahun ke belakang

        tahun_choices = [
            (f"{year}/{year+1}", f"{year}/{year+1}")
            for year in range(end_year, start_year - 1, -1)
        ]

        self.fields['Tahun_Pelajaran'].widget.choices = tahun_choices
        self.fields['Tahun_Pelajaran'].initial = f"{tahun_awal}/{tahun_awal + 1}"

        # Set default tanggal penetapan jika belum ada
        if not self.fields['tanggal_penetapan'].initial:
            self.fields['tanggal_penetapan'].initial = timezone.now().date()

    def clean_Tahun_Pelajaran(self):
        tahun_pelajaran = self.cleaned_data['Tahun_Pelajaran']
        
        # Validasi format dan tahun ajaran berurutan
        if '/' not in tahun_pelajaran:
            raise forms.ValidationError("Format harus 'YYYY/YYYY+1' (contoh: 2024/2025)!")
        
        try:
            tahun_awal, tahun_akhir = map(int, tahun_pelajaran.split('/'))
        except:
            raise forms.ValidationError("Tahun harus berupa angka dan format valid.")
        
        if tahun_akhir != tahun_awal + 1:
            raise forms.ValidationError("Tahun akhir harus tahun awal + 1 (contoh: 2024/2025)!")
        
        return tahun_pelajaran

    






class FormKelas(forms.ModelForm):
    class Meta:
        model = models.Kelas
        fields = ['Kelas']

        labels={
            "Kelas":"Kelas (contoh 7 dst)"
        }

        widgets = {
            'Nama_Lembaga': forms.Select(
                attrs={'class': 'form-select mb-3'}
            ),
            'Kelas': forms.TextInput(
                attrs={'class': 'form-control mb-3'}
            ),
        }

class FormRombel(forms.ModelForm):
    class Meta:
        model = models.Rombel_kelas
        fields = ['Kelas','Rombel']

        labels={
            "Kelas":"Kelas (contoh 7 dst)"
        }

        widgets = {
            'Rombel': forms.TextInput(
                attrs={'class': 'form-control mb-3'}
            ),
            'Kelas': forms.Select(
                attrs={'class': 'form-select mb-3'}
            ),
        }




class MatapelajaranForm(forms.ModelForm):
    class Meta:
        model = models.Matapelajaran
        fields = ['Nama_Mapel']

        widgets = {
                'Nama_Mapel': forms.TextInput(
                    attrs={'class': 'form-control'}
                ),
                
            }




class Form_Staff (UserCreationForm):
    password1 = forms.CharField(
        label= ("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password1",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    password2 = forms.CharField(
        label= ("Konfirmasi Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password2",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    
    class Meta :
        model = models.Pengguna
        fields = [
                "username",
                "Nama",
                "password1",
                "password2",
                
            ]
        help_texts = {
            'username': None,
            # "password1": None,
            # "password2": None,
        }

        
        labels={
                # 'Nama_Pengguna': 'Pengguna',
            }

        
        widgets = {
            'username': forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    
                }
            ),
            'Nama_Pengguna': forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                }
            ),
            "Nama": forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    
                }
            ),
        }


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:  # Minimal harus 6 karakter
            raise ValidationError("Username harus memiliki minimal 3 karakter.")
        return username



    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Validasi: Jika salah satu password diisi, kedua field harus sama
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')

        # Jika password diisi, set password baru
        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password harus memiliki minimal 8 karakter.")
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 huruf kapital.")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 angka.")
        return password
    





class Form_Ubah_Staff (forms.ModelForm):
    password1 = forms.CharField(
        label= ("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password1",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    password2 = forms.CharField(
        label= ("Konfirmasi Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password2",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    
    class Meta :
        model = models.Pengguna
        fields = [
                "username",
                "Nama",
                "password1",
                "password2",
                
            ]
        help_texts = {
            'username': None,
            # "password1": None,
            # "password2": None,
        }

        
        labels={
                # 'Nama_Pengguna': 'Pengguna',
            }

        
        widgets = {
            'username': forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    
                }
            ),
            'Nama_Pengguna': forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                }
            ),
            "Nama": forms.TextInput(
                attrs = {
                    'class':'form-control mb-3',
                    
                }
            ),
        }


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:  # Minimal harus 6 karakter
            raise ValidationError("Username harus memiliki minimal 3 karakter.")
        return username



    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Validasi: Jika salah satu password diisi, kedua field harus sama
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')

        # Jika password diisi, set password baru
        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password harus memiliki minimal 8 karakter.")
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 huruf kapital.")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 angka.")
        return password






class Form_siswa (UserCreationForm):
    password1 = forms.CharField(
        label= ("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password1",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    password2 = forms.CharField(
        label= ("Konfirmasi Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password2",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    
    class Meta :
        model = models.Pengguna
        fields = [
                "username",
                "Nama",
                "Kelas",
                "Rombel",
                "password1",
                "password2",
                
            ]
        help_texts = {
            'username': None,
            # "password1": None,
            # "password2": None,
        }

        
        labels={
                'Nama': 'Nama Siswa',
            }

        
        widgets = {
            'username': forms.TextInput(
                attrs = {
                    'placeholder':"Masukan NISN Anda harus 16 digit",
                    'class':'form-control mb-3',
                    
                }
            ),
            'Nama_Pengguna': forms.TextInput(
                attrs = {
                    'placeholder':"Nama Siswa",
                    'class':'form-control mb-3',
                }
            ),
            "Nama": forms.TextInput(
                attrs = {
                    'placeholder':"Nama Siswa",
                    'class':'form-control mb-3',
                    
                }
            ),
            "Kelas": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Rombel": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
        }


    def clean_username(self):
        username = self.cleaned_data.get('username')

        
        if not username.isdigit():
            raise ValidationError("Username (NISN) hanya boleh berisi angka.")

        username_length = len(username)
        if len(username) != 16:
            raise ValidationError(f"Username (NISN) harus memiliki 16 karakter, tetapi Anda memasukkan {username_length} karakter.")

        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Validasi: Jika salah satu password diisi, kedua field harus sama
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')

        # Jika password diisi, set password baru
        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password harus memiliki minimal 8 karakter.")
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 huruf kapital.")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 angka.")
        return password
    




class Form_Ubah_siswa (forms.ModelForm):
    password1 = forms.CharField(
        label= ("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password1",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    password2 = forms.CharField(
        label= ("Konfirmasi Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3',
                                            'type': 'password',
                                            'required': 'true',
                                            "id":"password2",
                                            'placeholder': 'password minimal 8 karakter, minimal 1 huruf kapital dan 1 angka'
        }),
        
    )
    
    class Meta :
        model = models.Pengguna
        fields = [
                "username",
                "Nama",
                "Kelas",
                "Rombel",
                "password1",
                "password2",
                
            ]
        help_texts = {
            'username': None,
            # "password1": None,
            # "password2": None,
        }

        
        labels={
                'Nama': 'Nama Siswa',
            }

        
        widgets = {
            'username': forms.TextInput(
                attrs = {
                    'placeholder':"Masukan NISN Anda harus 16 digit",
                    'class':'form-control mb-3',
                    
                }
            ),
            'Nama_Pengguna': forms.TextInput(
                attrs = {
                    'placeholder':"Nama Siswa",
                    'class':'form-control mb-3',
                }
            ),
            "Nama": forms.TextInput(
                attrs = {
                    'placeholder':"Nama Siswa",
                    'class':'form-control mb-3',
                    
                }
            ),
            "Kelas": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
            "Rombel": forms.Select(
                attrs = {
                    'class':'form-select mb-3',
                    
                }
            ),
        }


    def clean_username(self):
        username = self.cleaned_data.get('username')

        
        if not username.isdigit():
            raise ValidationError("Username (NISN) hanya boleh berisi angka.")

        username_length = len(username)
        if len(username) != 16:
            raise ValidationError(f"Username (NISN) harus memiliki 16 karakter, tetapi Anda memasukkan {username_length} karakter.")

        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Validasi: Jika salah satu password diisi, kedua field harus sama
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')

        # Jika password diisi, set password baru
        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password harus memiliki minimal 8 karakter.")
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 huruf kapital.")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password harus memiliki minimal 1 angka.")
        return password


class UploadForm(forms.Form):
    file = forms.FileField(
        label="Upload File CSV",
        widget=forms.FileInput(attrs={'class': 'form-control mt-2'}),
        required=True
    )

class UploadFormSoal(forms.Form):
    file_excel = forms.FileField(  # <-- ubah nama field jadi file_excel
        label="Upload File xls",
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'accept': '.xls,.xlsx,.ods,.xlsm',
            'class': 'form-control'
        })
    )