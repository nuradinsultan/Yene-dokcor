from django.db import models
from apps.users.models import CustomUser

class DoctorSpecialty(models.Model):
    name = models.CharField(max_length=100)
    name_am = models.CharField(max_length=100, blank=True) # Amharic name

    def __str__(self):
        return self.name

class DoctorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.ForeignKey(DoctorSpecialty, on_delete=models.SET_NULL, null=True)
    license_number = models.CharField(max_length=50, unique=True) # For verification
    bio = models.TextField(blank=True)
    # Location: Store kebele, woreda, city. Consider GeoDjango later.
    city = models.CharField(max_length=100, default="Addis Ababa")
    woreda = models.CharField(max_length=100, blank=True)
    kebele = models.CharField(max_length=100, blank=True)
    # Availability is simple for MVP: e.g., "Mon, Wed, Fri 2PM-5PM"
    availability = models.TextField(help_text="Describe your general weekly availability")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} - {self.specialty}"
