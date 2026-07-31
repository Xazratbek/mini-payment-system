from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    address = models.TextField(null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)

    def __str__(self):
        return f"{self.get_full_name()}"