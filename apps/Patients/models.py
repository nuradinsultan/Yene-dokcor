from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.users.models import CustomUser
import uuid

class PatientProfile(models.Model):
    # Basic Information
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    MRN = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name=models.CharField(max_length=100, blank=True)
    father_name=models.CharField(max_length=100, blank=True)
    last_name=models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Demographic Information
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    blood_type = models.CharField(max_length=3, blank=True, choices=[
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ])
    
    # Contact Information
    phone_number = models.CharField(max_length=15, blank=True)
    alternate_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, blank=True, default='USA')
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Medical Information
    primary_care_physician = models.CharField(max_length=200, blank=True)
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_id = models.CharField(max_length=50, blank=True)
    allergies = models.TextField(blank=True, help_text="List all known allergies")
    current_medications = models.TextField(blank=True, help_text="Current medications and dosages")
    chronic_conditions = models.TextField(blank=True, help_text="Chronic medical conditions")
    
    # Medical History
    surgical_history = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    
    # Preferences and Consent
    preferred_pharmacy = models.CharField(max_length=200, blank=True)
    consent_for_treatment = models.BooleanField(default=False)
    data_sharing_consent = models.BooleanField(default=False)
    
    # Status and Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_medical_update = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username} ({self.patient_id})"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def is_minor(self):
        return self.age is not None and self.age < 18
    
    def update_medical_info(self):
        self.last_medical_update = timezone.now()
        self.save()
    
    def get_emergency_info(self):
        return {
            'name': self.emergency_contact_name,
            'phone': self.emergency_contact_phone,
            'relationship': self.emergency_contact_relationship
        }

class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records')
    record_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    record_type = models.CharField(max_length=100, choices=[
        ('consultation', 'Consultation'),
        ('lab_result', 'Lab Result'),
        ('imaging', 'Imaging'),
        ('prescription', 'Prescription'),
        ('vaccination', 'Vaccination'),
        ('surgery', 'Surgery'),
        ('other', 'Other'),
    ])
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='medical_records/%Y/%m/%d/', blank=True, null=True)
    date_of_service = models.DateField()
    provider = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_of_service', '-created_at']
    
    def __str__(self):
        return f"{self.record_type}: {self.title} - {self.patient}"

class VitalSigns(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='vital_signs')
    recorded_at = models.DateTimeField(default=timezone.now)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(70), MaxValueValidator(200)])
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(40), MaxValueValidator(130)])
    heart_rate = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(40), MaxValueValidator(200)])
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(35), MaxValueValidator(42)])
    oxygen_saturation = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(70), MaxValueValidator(100)])
    respiratory_rate = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(8), MaxValueValidator(40)])
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    height = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Height in meters")
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = "Vital Signs"
    
    @property
    def bmi(self):
        if self.weight and self.height and self.height > 0:
            return round(self.weight / (self.height ** 2), 1)
        return None
    
    def __str__(self):
        return f"Vitals for {self.patient} at {self.recorded_at}"

class Appointment(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    scheduled_for = models.DateTimeField()
    duration = models.DurationField(default=timezone.timedelta(minutes=30))
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], default='scheduled')
    provider = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_for']
    
    def __str__(self):
        return f"Appointment: {self.patient} - {self.scheduled_for}"

class Medication(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribed_by = models.CharField(max_length=200, blank=True)
    reason = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_active', '-start_date']
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} - {self.patient} ({status})"
