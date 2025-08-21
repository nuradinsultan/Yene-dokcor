import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimeStampedModel

class CustomUserManager(BaseUserManager):
    """Custom user manager for phone number-based authentication"""
    
    def create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a regular user with the given phone number and password"""
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create and save a SuperUser with the given phone number and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractUser, BaseModel):
    """Advanced Custom User Model with comprehensive healthcare features"""
    
    class UserType(models.TextChoices):
        PATIENT = 'PATIENT', _('Patient')
        DOCTOR = 'DOCTOR', _('Doctor')
        ADMIN = 'ADMIN', _('Administrator')
        LAB_TECH = 'LAB_TECH', _('Lab Technician')
        PHARMACIST = 'PHARMACIST', _('Pharmacist')
        NURSE = 'NURSE', _('Nurse')
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = PhoneNumberField(
        unique=True, 
        region='ET', 
        verbose_name=_("Phone Number"),
        help_text=_("Format: +251XXXXXXXXX")
    )
    email = models.EmailField(
        _("Email Address"), 
        blank=True, 
        null=True,
        db_index=True
    )
    
    # User Type and Roles
    user_type = models.CharField(
        _("User Type"),
        max_length=20,
        choices=UserType.choices,
        default=UserType.PATIENT
    )
    roles = models.ManyToManyField(
        'Role',
        verbose_name=_("Roles"),
        blank=True,
        related_name='users'
    )
    
    # Verification & Status
    is_verified = models.BooleanField(_("Verified"), default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_date = models.DateTimeField(_("Verification Date"), blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Profile Information
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('N', _('Prefer not to say')),
    ]
    
    date_of_birth = models.DateField(_("Date of Birth"), blank=True, null=True)
    gender = models.CharField(
        _("Gender"),
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    profile_picture = models.ImageField(
        _("Profile Picture"),
        upload_to='profile_pictures/%Y/%m/%d/',
        blank=True,
        null=True,
        max_length=500
    )
    bio = models.TextField(_("Bio"), blank=True, null=True, max_length=1000)
    
    # Contact Information
    emergency_contact_name = models.CharField(
        _("Emergency Contact Name"),
        max_length=100,
        blank=True,
        null=True
    )
    emergency_contact_phone = PhoneNumberField(
        _("Emergency Contact Phone"),
        region='ET',
        blank=True,
        null=True
    )
    emergency_contact_relation = models.CharField(
        _("Emergency Contact Relation"),
        max_length=50,
        blank=True,
        null=True
    )
    
    address = models.TextField(_("Address"), blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    state = models.CharField(_("State/Region"), max_length=100, blank=True, null=True)
    zip_code = models.CharField(_("ZIP Code"), max_length=20, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, default='Ethiopia')
    
    # Consent & Preferences
    terms_accepted = models.BooleanField(_("Terms Accepted"), default=False)
    terms_accepted_date = models.DateTimeField(_("Terms Accepted Date"), blank=True, null=True)
    privacy_policy_accepted = models.BooleanField(_("Privacy Policy Accepted"), default=False)
    marketing_consent = models.BooleanField(_("Marketing Consent"), default=False)
    
    notification_preferences = models.JSONField(
        _("Notification Preferences"),
        default=dict,
        help_text=_("User's notification preferences in JSON format")
    )
    
    # Security
    failed_login_attempts = models.PositiveIntegerField(_("Failed Login Attempts"), default=0)
    last_failed_login = models.DateTimeField(_("Last Failed Login"), blank=True, null=True)
    password_changed_date = models.DateTimeField(_("Password Changed Date"), blank=True, null=True)
    last_password_reset = models.DateTimeField(_("Last Password Reset"), blank=True, null=True)
    
    # Metadata
    device_info = models.JSONField(
        _("Device Information"),
        blank=True,
        null=True,
        help_text=_("Information about user's device")
    )
    last_login_ip = models.GenericIPAddressField(_("Last Login IP"), blank=True, null=True)
    registration_ip = models.GenericIPAddressField(_("Registration IP"), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    last_login = models.DateTimeField(_("Last Login"), blank=True, null=True)
    last_activity = models.DateTimeField(_("Last Activity"), blank=True, null=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_activity']),
        ]
        permissions = [
            ('view_user_statistics', _('Can view user statistics')),
            ('export_user_data', _('Can export user data')),
            ('manage_user_roles', _('Can manage user roles')),
        ]
    
    def __str__(self):
        return f"{self.phone_number} - {self.get_full_name() or self.username}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(_("Date of birth cannot be in the future"))
        
        if self.emergency_contact_phone and self.emergency_contact_phone == self.phone_number:
            raise ValidationError(_("Emergency contact phone cannot be the same as your phone number"))
    
    def save(self, *args, **kwargs):
        """Override save method for additional logic"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        """Return the full name of the user."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() if full_name.strip() else self.username
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username
    
    @property
    def age(self):
        """Calculate user's age from date of birth."""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def is_medical_professional(self):
        """Check if user is any type of medical professional."""
        medical_types = [self.UserType.DOCTOR, self.UserType.NURSE, 
                        self.UserType.LAB_TECH, self.UserType.PHARMACIST]
        return self.user_type in medical_types
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.roles.filter(name=role_name).exists()
    
    def get_primary_role(self):
        """Get the user's primary role based on user type."""
        return self.roles.filter(is_primary=True).first()
    
    def increment_failed_login_attempts(self):
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
    
    def reset_failed_login_attempts(self):
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
    
    def update_last_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

class Role(TimeStampedModel):
    """Role model for user permissions and access control"""
    
    name = models.CharField(_("Role Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_("Permissions"),
        blank=True,
        related_name='roles'
    )
    is_primary = models.BooleanField(_("Is Primary Role"), default=False)
    is_default = models.BooleanField(_("Is Default Role"), default=False)
    
    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ['name']
    
    def __str__(self):
        return self.name

class UserActivityLog(TimeStampedModel):
    """Model to track user activities and audit trails"""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'LOGIN', _('Login')
        LOGOUT = 'LOGOUT', _('Logout')
        PROFILE_UPDATE = 'PROFILE_UPDATE', _('Profile Update')
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', _('Password Change')
        APPOINTMENT_CREATE = 'APPOINTMENT_CREATE', _('Appointment Created')
        APPOINTMENT_UPDATE = 'APPOINTMENT_UPDATE', _('Appointment Updated')
        MEDICAL_RECORD_ACCESS = 'MEDICAL_RECORD_ACCESS', _('Medical Record Accessed')
        PAYMENT_PROCESSED = 'PAYMENT_PROCESSED', _('Payment Processed')
        SECURITY_EVENT = 'SECURITY_EVENT', _('Security Event')
        SYSTEM_EVENT = 'SYSTEM_EVENT', _('System Event')
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='activity_logs',
        verbose_name=_("User")
    )
    activity_type = models.CharField(
        _("Activity Type"),
        max_length=50,
        choices=ActivityType.choices
    )
    description = models.TextField(_("Description"))
    ip_address = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    user_agent = models.TextField(_("User Agent"), blank=True, null=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    severity = models.CharField(
        _("Severity"),
        max_length=20,
        choices=[
            ('INFO', _('Info')),
            ('WARNING', _('Warning')),
            ('ERROR', _('Error')),
            ('CRITICAL', _('Critical')),
        ],
        default='INFO'
    )
    
    class Meta:
        verbose_name = _("User Activity Log")
        verbose_name_plural = _("User Activity Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.activity_type} - {self.created_at}"

class UserSession(TimeStampedModel):
    """Model to track user sessions and devices"""
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='sessions',
        verbose_name=_("User")
    )
    session_key = models.CharField(_("Session Key"), max_length=40, unique=True)
    device_type = models.CharField(_("Device Type"), max_length=50, blank=True, null=True)
    device_name = models.CharField(_("Device Name"), max_length=100, blank=True, null=True)
    os = models.CharField(_("Operating System"), max_length=50, blank=True, null=True)
    browser = models.CharField(_("Browser"), max_length=50, blank=True, null=True)
    device_info = models.JSONField(_("Device Information"), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    login_time = models.DateTimeField(_("Login Time"), auto_now_add=True)
    last_activity = models.DateTimeField(_("Last Activity"), auto_now=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    expires_at = models.DateTimeField(_("Expires At"))
    
    class Meta:
        verbose_name = _("User Session")
        verbose_name_plural = _("User Sessions")
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.session_key}"
    
    def is_expired(self):
        """Check if session is expired"""
        return timezone.now() > self.expires_at

class UserVerification(TimeStampedModel):
    """Model to handle user verification processes"""
    
    class VerificationMethod(models.TextChoices):
        SMS = 'SMS', _('SMS')
        EMAIL = 'EMAIL', _('Email')
        MANUAL = 'MANUAL', _('Manual')
    
    class VerificationType(models.TextChoices):
        PHONE = 'PHONE', _('Phone Verification')
        EMAIL = 'EMAIL', _('Email Verification')
        IDENTITY = 'IDENTITY', _('Identity Verification')
        MEDICAL = 'MEDICAL', _('Medical License Verification')
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='verifications',
        verbose_name=_("User")
    )
    verification_type = models.CharField(
        _("Verification Type"),
        max_length=20,
        choices=VerificationType.choices
    )
    method = models.CharField(
        _("Verification Method"),
        max_length=10,
        choices=VerificationMethod.choices,
        default=VerificationMethod.SMS
    )
    token = models.CharField(_("Verification Token"), max_length=100)
    is_used = models.BooleanField(_("Is Used"), default=False)
    expires_at = models.DateTimeField(_("Expires At"))
    verified_at = models.DateTimeField(_("Verified At"), blank=True, null=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("User Verification")
        verbose_name_plural = _("User Verifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'verification_type']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
        unique_together = ['user', 'verification_type', 'is_used']
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.verification_type}"
    
    def is_expired(self):
        """Check if verification token is expired"""
        return timezone.now() > self.expires_at
    
    def mark_as_used(self):
        """Mark verification as used"""
        self.is_used = True
        self.verified_at = timezone.now()
        self.save()

# Signal imports and handlers
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import user_logged_in, user_logged_out

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create corresponding profile when user is created"""
    if created:
        # Create appropriate profile based on user type
        if instance.user_type == CustomUser.UserType.DOCTOR:
            from apps.doctors.models import DoctorProfile
            DoctorProfile.objects.create(user=instance)
        elif instance.user_type == CustomUser.UserType.PATIENT:
            from apps.patients.models import PatientProfile
            PatientProfile.objects.create(user=instance)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login activity"""
    UserActivityLog.objects.create(
        user=user,
        activity_type=UserActivityLog.ActivityType.LOGIN,
        description=f"User logged in from {request.META.get('REMOTE_ADDR')}",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout activity"""
    UserActivityLog.objects.create(
        user=user,
        activity_type=UserActivityLog.ActivityType.LOGOUT,
        description=f"User logged out from {request.META.get('REMOTE_ADDR')}",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
