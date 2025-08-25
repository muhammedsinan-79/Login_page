from rest_framework.throttling import AnonRateThrottle
from django.core.cache import cache
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

class EmailRateThrottle(AnonRateThrottle):

    scope = 'email'

    def get_cache_key(self, request, view):
        #generate cache key based on email address from request data

        email = None
        if hasattr(request, 'data') and request.data:
            email = request.data.get('email')
        elif request.method == 'POST' and hasattr(request, 'POST'):
            email = request.POST.get('email')            
        if not email:
            return None
        return f"throttle_{self.scope}_{email}"#create unique cache key for this email , self.scope--> use scope dynamically
    
    def get_rate(self):  #fetech rate limit from setting.py

        if not getattr(self , 'scope' , None):
            return None
        try:
            return self.THROTTLE_RATES[self.scope]
        except KeyError:
            return None
        
class ForgotPasswordEmailThrottle(EmailRateThrottle):

    scope = 'forgot_password_email'   #this line only need if self.scope used (scope is overrided here)

class IpRateLimiting(EmailRateThrottle):

    scope = 'ip_limit'

    def get_cache_key(self, request, view): #override
        ip = request.META.get('REMOTE_ADDR')
        print(ip,"throttled")
        if not ip:
            return None
        return f"throttle_{self.scope}_{ip}"





