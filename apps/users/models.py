from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid

class CustomUser(AbstractUser):
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = PhoneNumberField(unique=True, region='ET', verbose_name=_("Phone Number"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email Address"))
    first_name = models.TextField(blank=True, null=True, verbose_name=_("first name"))
    Fath_name = models.TextField(blank=True, null=True, verbose_name=_("father name"))
    username = models.TextField(blank=True, null=True, verbose_name=_("username"))
    
    # User Type Flags
    is_doctor = models.BooleanField(default=False, verbose_name=_("Is Doctor"))
    is_patient = models.BooleanField(default=False, verbose_name=_("Is Patient"))
    is_admin_staff = models.BooleanField(default=False, verbose_name=_("Is Admin Staff"))
    is_lab_technician = models.BooleanField(default=False, verbose_name=_("Is Lab Technician"))
    
    # Verification & Status
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    # Profile Information
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('N', _('Prefer not to say')),
    ]
    
    date_of_birth = models.DateField(blank=True, null=True, verbose_name=_("Date of Birth"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name=_("Profile Picture")
    )
    
    # Contact Information
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = PhoneNumberField(blank=True, null=True, region='ET')
    address = models.TextField(blank=True, null=True, verbose_name=_("Address"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    last_login = models.DateTimeField(blank=True, null=True, verbose_name=_("Last Login"))
    
    # Consent & Preferences
    terms_accepted = models.BooleanField(default=False, verbose_name=_("Terms Accepted"))
    privacy_policy_accepted = models.BooleanField(default=False, verbose_name=_("Privacy Policy Accepted"))
    marketing_consent = models.BooleanField(default=False, verbose_name=_("Marketing Consent"))
    notification_preferences = models.JSONField(
        default=dict,
        verbose_name=_("Notification Preferences"),
        help_text=_("User's notification preferences in JSON format")
    )
    
    # Security
    failed_login_attempts = models.PositiveIntegerField(default=0, verbose_name=_("Failed Login Attempts"))
    last_failed_login = models.DateTimeField(blank=True, null=True, verbose_name=_("Last Failed Login"))
    password_changed_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Password Changed Date"))
    
    # Metadata
    device_info = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("Device Information"),
        help_text=_("Information about user's device")
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name=_("IP Address"))
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.phone_number} - {self.get_full_name() or self.username}"
    
    def get_full_name(self):
        """Return the full name of the user."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() if full_name.strip() else self.username
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username
    
    def is_medical_staff(self):
        """Check if user is any type of medical staff."""
        return self.is_doctor or self.is_lab_technician or self.is_admin_staff
    
    def get_user_type(self):
        """Return the user type as a string."""
        if self.is_doctor:
            return "doctor"
        elif self.is_patient:
            return "patient"
        elif self.is_lab_technician:
            return "lab_technician"
        elif self.is_admin_staff:
            return "admin_staff"
        return "unknown"
    
    def increment_failed_login_attempts(self):
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login_attempts(self):
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])
    
    @property
    def age(self):
        """Calculate user's age from date of birth."""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

class UserActivityLog(models.Model):
    """Model to track user activities"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=100, verbose_name=_("Activity Type"))
    description = models.TextField(verbose_name=_("Description"))
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("User Activity Log")
        verbose_name_plural = _("User Activity Logs")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.activity_type} - {self.timestamp}"

class UserSession(models.Model):
    """Model to track user sessions"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("User Session")
        verbose_name_plural = _("User Sessions")
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.session_key}"
