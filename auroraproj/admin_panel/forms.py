from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from .models import AdminRole
import re

class AdminLoginForm(forms.Form):
    """Enhanced admin login form"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox'
        })
    )

class AdminPasswordResetForm(forms.Form):
    """Admin password reset request form"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your email address'
        })
    )

class AdminPasswordChangeForm(forms.Form):
    """Admin password change form with strong password requirements"""
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Current password (leave blank for reset)'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'New password'
        }),
        validators=[MinLengthValidator(8)]
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm new password'
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Make current password required if user is changing password (not resetting)
        if user and not kwargs.get('data'):
            self.fields['current_password'].required = True
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        # Strong password requirements
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        current_password = cleaned_data.get('current_password')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Passwords don't match.")
        
        # Check current password if user is changing (not resetting)
        if self.user and current_password:
            if not self.user.check_password(current_password):
                raise ValidationError("Current password is incorrect.")
        
        return cleaned_data

class AdminUserCreationForm(UserCreationForm):
    """Form for creating admin users"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    employee_id = forms.CharField(max_length=20, required=True)
    department = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ModelChoiceField(queryset=AdminRole.objects.filter(is_active=True), required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input input-bordered w-full'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        
        return user

class AdminUserUpdateForm(forms.ModelForm):
    """Form for updating admin users"""
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    role = forms.ModelChoiceField(queryset=AdminRole.objects.filter(is_active=True), required=False)
    department = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input input-bordered w-full'})
        
        # Pre-populate fields
        if self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['email'].initial = self.instance.email
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name

class AdminRoleForm(forms.ModelForm):
    """Form for managing admin roles"""
    class Meta:
        model = AdminRole
        fields = ['name', 'description', 'permissions', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'permissions': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'input input-bordered w-full'})
        self.fields['is_active'].widget.attrs.update({'class': 'checkbox'})
