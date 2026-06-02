
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name_plural = 'Categories'
    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Level(models.Model):
    name = models.CharField(max_length=20) 
    def __str__(self):
        return self.name

class Term(models.Model):
    name = models.CharField(max_length=20) 
    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books')
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    level = models.ForeignKey(Level, null=True, blank=True, on_delete=models.SET_NULL)
    term = models.ForeignKey(Term, null=True, blank=True, on_delete=models.SET_NULL)
    author = models.CharField(max_length=100, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='books/%Y/%m/%d', blank=True)
    def __str__(self):
        return self.title
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.count() > 0:
            return sum(r.rating for r in ratings) / ratings.count()
        return 0

class Rating(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('book', 'user')
    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.rating}"

class Membership(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("rejected", "Rejected"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    start_date = models.DateField()
    end_date = models.DateField()
    borrow_limit = models.PositiveIntegerField(default=0)
    fine_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    student_card = models.ImageField(upload_to="student_cards/", null=True, blank=True)
    def __str__(self):
        return f"{self.user.username}: {'Active' if self.status == 'active' else 'Inactive'}"

class BorrowRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('returned', 'Returned'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    return_date = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"
    
    class Meta:
        ordering = ['-request_date']
        
    def is_active(self):
        return self.status in ['pending', 'approved']    




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    student_card = models.ImageField(upload_to='student_cards/', blank=True, null=True)  # NEW

    def __str__(self):
        return self.user.username
