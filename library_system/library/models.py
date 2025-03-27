from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

User = get_user_model()

class Category(models.Model):
    """Model for book categories/genres"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Book(models.Model):
    """Model representing books in the library"""
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField('ISBN', max_length=13, unique=True)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name='books')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    available = models.PositiveIntegerField(default=1)
    publication_date = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['isbn']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    def get_absolute_url(self):
        return reverse('book-detail', kwargs={'pk': self.pk})

    @property
    def is_available(self):
        return self.available > 0

    def save(self, *args, **kwargs):
        if not self.pk:  # New book being added
            self.available = self.quantity
        super().save(*args, **kwargs)

class Loan(models.Model):
    """Model for tracking book loans"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    checkout_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)
    
    LOAN_STATUS = (
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    )
    status = models.CharField(max_length=10, choices=LOAN_STATUS, default='active')
    
    class Meta:
        ordering = ['-checkout_date']
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'
    
    def __str__(self):
        return f"{self.book.title} - {self.user.get_full_name()}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date and not self.returned_date
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now() - self.due_date).days
        return 0

class Review(models.Model):
    """Model for user book reviews"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.book.title} - {self.rating} stars"
    
    @property
    def stars(self):
        return range(self.rating)

class ActivityLog(models.Model):
    """Model for tracking system activities"""
    ACTION_CHOICES = (
        ('checkout', 'Book Checkout'),
        ('return', 'Book Return'),
        ('review', 'Review Posted'),
        ('user', 'User Activity'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.timestamp}"
