from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    
    # Additional fields
    is_librarian = models.BooleanField(
        _('librarian status'),
        default=False,
        help_text=_('Designates whether the user can access librarian features.')
    )
    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('User contact phone number.')
    )
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pics/',
        null=True,
        blank=True
    )
    
    # Add any additional fields here
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.get_full_name() or self.username
