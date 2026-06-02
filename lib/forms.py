from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Rating, BorrowRequest, Membership, Book, Profile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class BorrowRequestForm(forms.ModelForm):
    class Meta:
        model = BorrowRequest
        fields = []  # All handled in view

class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = []  

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'slug', 'category', 'department', 'level', 'term',
            'author', 'isbn', 'description', 'price', 'stock',
            'available', 'image'
        ]

class ReturnForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={"class": "form-select select2-user"})
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        widget=forms.Select(attrs={"class": "form-select select2-book"})
    )
    STATUS_CHOICES = (
        ("in_time", "In time"),
        ("delay", "Delay"),
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect
    )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone', 'address', 'student_card']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,                    
                'style': 'resize: vertical; max-height: 120px;',  
            }),
            'student_card': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
