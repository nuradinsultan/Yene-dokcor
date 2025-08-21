from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class CustomUser(AbstractUser):
    # Use phone number as primary user identifier
    phone_number = PhoneNumberField(unique=True, region='ET') # Format: +251...
    email = models.EmailField(blank=True, null=True)
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False) # Crucial for doctors
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number' # Now log in with phone number
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.phone_number} - {self.username}"
