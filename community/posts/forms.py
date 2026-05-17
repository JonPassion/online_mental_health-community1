from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    title = forms.CharField(
        label='Title',
        max_length=150,
        widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter a short title for your post'
        })
    )
    content = forms.CharField(
        label='Content',
        widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 6,
        'placeholder': 'Share your thoughts, experiences, or advice...'
        })
    )

    class Meta:
        model = Post
        fields = ['title', 'content']