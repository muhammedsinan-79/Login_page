from django.db import models

# Create your models here.

'''class LoginInfo(models.Model):
    
    def __str__(self):
        return self.user_email
    
class SignupInfo(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(unique=True)
    user_password = models.CharField(max_length=100)

    def __str__(self):
        return self.user_email'''


class RateLimitLog(models.Model):
    email = models.EmailField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_throttled = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __strt__(self):
        return f"{self.email} @ {self.timestamp} from {self.ip_address}"
    
class InvalidCredentialsLog(models.Model):
    email = models.EmailField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_throttled = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True) 

    def __strt__(self):
        return f"{self.email} @ {self.timestamp} from {self.ip_address}"
    
class LoginCredentialLog(models.Model):
    email = models.EmailField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)    

    def __strt__(self):
        return f"{self.email} @ {self.timestamp} from {self.ip_address}"     