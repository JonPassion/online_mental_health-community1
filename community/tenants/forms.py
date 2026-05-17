from django import forms
from django.core.exceptions import ValidationError
from .models import Tenant, TenantDomain, TenantSettings
import re


class TenantCreationForm(forms.ModelForm):
    """Form for creating a new tenant"""
    domain = forms.CharField(
        max_length=255,
        help_text="Domain name (e.g., company.yourapp.com)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'company.yourapp.com'
        })
    )
    
    class Meta:
        model = Tenant
        fields = ['name', 'subscription_plan', 'max_users']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name'
            }),
            'subscription_plan': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_users': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription_plan'].choices = [
            ('free', 'Free (Max 10 users)'),
            ('basic', 'Basic (Max 50 users)'),
            ('premium', 'Premium (Max 200 users)'),
            ('enterprise', 'Enterprise (Unlimited users)'),
        ]
    
    def clean_domain(self):
        domain = self.cleaned_data.get('domain')
        
        if not domain:
            raise ValidationError('Domain is required.')
        
        # Basic domain validation
        domain_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not domain_pattern.match(domain):
            raise ValidationError('Please enter a valid domain name.')
        
        # Check if domain already exists
        if TenantDomain.objects.filter(domain=domain).exists():
            raise ValidationError('This domain is already in use.')
        
        return domain.lower()
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('Tenant name is required.')
        
        # Check if tenant name already exists
        if Tenant.objects.filter(name=name).exists():
            raise ValidationError('A tenant with this name already exists.')
        
        return name
    
    def clean_max_users(self):
        max_users = self.cleaned_data.get('max_users')
        subscription_plan = self.cleaned_data.get('subscription_plan')
        
        if subscription_plan == 'free' and max_users > 10:
            raise ValidationError('Free plan allows maximum 10 users.')
        elif subscription_plan == 'basic' and max_users > 50:
            raise ValidationError('Basic plan allows maximum 50 users.')
        elif subscription_plan == 'premium' and max_users > 200:
            raise ValidationError('Premium plan allows maximum 200 users.')
        
        return max_users


class TenantSettingsForm(forms.ModelForm):
    """Form for editing tenant settings"""
    class Meta:
        model = TenantSettings
        fields = [
            'allow_registration', 
            'require_email_verification',
            'default_user_role',
            'theme_color',
            'logo_url',
            'custom_css'
        ]
        widgets = {
            'allow_registration': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_email_verification': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'default_user_role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'theme_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/logo.png'
            }),
            'custom_css': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter custom CSS...'
            })
        }
    
    def clean_theme_color(self):
        color = self.cleaned_data.get('theme_color')
        
        if color:
            # Validate hex color
            color_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
            if not color_pattern.match(color):
                raise ValidationError('Please enter a valid hex color (e.g., #007bff).')
        
        return color
    
    def clean_logo_url(self):
        logo_url = self.cleaned_data.get('logo_url')
        
        if logo_url:
            # Basic URL validation
            if not logo_url.startswith(('http://', 'https://')):
                raise ValidationError('Logo URL must start with http:// or https://')
        
        return logo_url


class TenantUserForm(forms.Form):
    """Form for adding users to tenant"""
    username = forms.CharField(
        max_length=150,
        help_text="Username of the user to add",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('member', 'Member'),
            ('moderator', 'Moderator'),
            ('admin', 'Admin'),
        ],
        initial='member',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('Username is required.')
        
        # Check if user exists
        from django.contrib.auth.models import User
        if not User.objects.filter(username=username).exists():
            raise ValidationError('User with this username does not exist.')
        
        return username
