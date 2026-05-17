from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.core.exceptions import ValidationError


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
    required=True,
    widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))

    first_name = forms.CharField(
    required=False,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )

    last_name = forms.CharField(
    required=False,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Choose a username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})


class UserForm(forms.ModelForm):
    """Form for editing user basic information"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.instance.username
        
        # Check if email is unique (excluding current user)
        if User.objects.exclude(username=username).filter(email=email).exists():
            raise ValidationError('This email is already in use.')
        
        return email


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Tell us about yourself...',
            'class': 'form-control'
        }),
        required=False,
        max_length=500
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your location',
            'class': 'form-control'
        })
    )
    
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'placeholder': 'https://yourwebsite.com',
            'class': 'form-control'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (555) 123-4567',
            'class': 'form-control'
        })
    )
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text='Upload a profile picture (JPG, PNG, max 5MB)'
    )
    
    cover_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text='Upload a cover picture (JPG, PNG, max 10MB)'
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'website', 'phone', 
            'birth_date', 'profile_picture', 'cover_picture'
        ]
    
    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        
        if profile_picture:
            # Check if it's a newly uploaded file (has content_type attribute)
            if hasattr(profile_picture, 'content_type'):
                # Check file size (5MB max)
                if profile_picture.size > 5 * 1024 * 1024:
                    raise ValidationError('Profile picture must be less than 5MB.')
                
                # Check file type
                if not profile_picture.content_type.startswith('image/'):
                    raise ValidationError('File must be an image.')
        
        return profile_picture
    
    def clean_cover_picture(self):
        cover_picture = self.cleaned_data.get('cover_picture')
        
        if cover_picture:
            # Check if it's a newly uploaded file (has content_type attribute)
            if hasattr(cover_picture, 'content_type'):
                # Check file size (10MB max)
                if cover_picture.size > 10 * 1024 * 1024:
                    raise ValidationError('Cover picture must be less than 10MB.')
                
                # Check file type
                if not cover_picture.content_type.startswith('image/'):
                    raise ValidationError('File must be an image.')
        
        return cover_picture
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Basic phone validation
            import re
            phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
            if not phone_pattern.match(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
                raise ValidationError('Please enter a valid phone number.')
        
        return phone
    
    def clean_website(self):
        website = self.cleaned_data.get('website')
        
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        return website


class ProfilePictureUploadForm(forms.ModelForm):
    """Form for quick profile picture upload"""
    profile_picture = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['profile_picture']


class CoverPictureUploadForm(forms.ModelForm):
    """Form for quick cover picture upload"""
    cover_picture = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['cover_picture']