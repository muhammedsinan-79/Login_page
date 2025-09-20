from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from rest_framework.exceptions import Throttled
import time , logging

logger = logging.getLogger(__name__)
from .logging_config import logger


# class ProgressiveEmailThrottle(BaseThrottle):
#     scope = "email"
#     cache_format = "throttle_%(scope)s_%(ident)s"

#     def get_cache_key(self, request, view):
#         #generate cache key based on email address from request data
#         email = None
#         email = request.data.get("email")
#         if not email:
#             return None
#         return self.cache_format % {"scope": self.scope, "ident": email}
    
#     def allow_request(self, request, view):

#         self.key = self.get_cache_key(request,view)
#         if self.key is None:
#             return True
        
#         rest_time = 3600
#         max_attempt = 5
#         base_time = 60

#         throttle_history = cache.get(
#             self.key,{"attempt":0, "next_allowed_time":0,"last_request_time":0}
#             )
#         current_time = time.time()
#         print("current time",current_time)

#         #logging

#         logger.info(f"[THROTTLE][READ] key={self.key}, history={throttle_history}, now={current_time}")


#         if throttle_history["attempt"] >= max_attempt:
#             print("throttled for max attempt time",current_time)
#             wait_time = (rest_time - (current_time - throttle_history["last_request_time"]))
#             print(wait_time)
#             logger.warning(f"[THROTTLE][BLOCK] key={self.key}, attempts={throttle_history['attempt']}, wait={wait_time}s")
#             raise Throttled(detail="Too many attempts. Please try again after 1 hour.")

        
#         if throttle_history["next_allowed_time"] > current_time:
#             self.wait_time = throttle_history["next_allowed_time"] -  current_time      
#             logger.warning(f"[THROTTLE][WAIT] key={self.key}, must wait={self.wait_time:.1f}s, history={throttle_history}")
#             wait_time = int(throttle_history["next_allowed_time"] - current_time)

#             minutes, seconds = divmod(wait_time, 60)
#             if minutes > 0:
#                 formatted_time = f"{minutes} min {seconds} seconds"
#             else:
#                 formatted_time = f"{seconds} seconds"
            
#             raise Throttled(#wait=wait_time,
#                 detail=f"Resend Available after {formatted_time} ")

#             # return False #self.throttle_failure()
            
#         # Calculate wait_time BEFORE incrementing attempt
#         wait_time = base_time * (2 ** throttle_history["attempt"])

#         attempt_key = f"{self.key}:attempt"
#         key = f"{self.key}:attempt"
#         if cache.get(key) is None:  #change to cache.incr
#             cache.set(key, 0, timeout=3600)  
#         throttle_history["attempt"] = cache.incr(key, 1)


#         # throttle_history["attempt"] += 1
#         throttle_history["last_request_time"] = current_time
#         throttle_history["next_allowed_time"] = current_time + wait_time
        
#         print("throttle history for allowed request , ",throttle_history)
#         ttl = max(wait_time + 5, rest_time)
#         cache.set(self.key , throttle_history, timeout=ttl)

#         logger.info(f"[THROTTLE][WRITE] key={self.key}, history={throttle_history}, ttl={ttl}s")

#         return True  #super().allow_request(request, view)
    
#     def wait(self):
#         return getattr(self, "wait_time", 60)

class ExponentialEmailThrottle(BaseThrottle):
   
    
    def __init__(self):
        self.base_wait_time = getattr(settings, 'EMAIL_BASE_WAIT_TIME', 60)  # 1 minute
        self.max_attempts = getattr(settings, 'EMAIL_MAX_ATTEMPTS', 8)  # Limit due to exponential growth
        self.reset_period = getattr(settings, 'EMAIL_RESET_PERIOD', 3600)  # 1 hour
    
    def allow_request(self, request, view):
        ident = self.get_ident(request)
        cache_key = f"email_throttle_exp_{ident}"
        
        throttle_data = cache.get(cache_key, {
            'attempts': 0,
            'last_request_time': 0,
            'next_allowed_time': 0
        })
        
        current_time = time.time()
        
        # Reset if enough time has passed
        if current_time - throttle_data['last_request_time'] > self.reset_period:
            throttle_data = {
                'attempts': 0,
                'last_request_time': 0,
                'next_allowed_time': 0
            }
        
        # Check max attempts
        if throttle_data['attempts'] >= self.max_attempts:
            return False
        
        # Check if enough time has passed
        if current_time < throttle_data['next_allowed_time']:
            return False
        
        # Update throttle data
        throttle_data['attempts'] += 1
        throttle_data['last_request_time'] = current_time
        
        # Exponential backoff: 2^(attempts-1) * base_wait_time
        wait_time = self.base_wait_time * (2 ** (throttle_data['attempts'] - 1))
        throttle_data['next_allowed_time'] = current_time + wait_time
        
        cache.set(cache_key, throttle_data, timeout=self.reset_period)
        
        return True
    
    def wait(self):
        ident = self.get_ident(self.request)
        cache_key = f"email_throttle_exp_{ident}"
        throttle_data = cache.get(cache_key)
        
        if throttle_data:
            current_time = time.time()
            wait_time = throttle_data['next_allowed_time'] - current_time
            return max(0, wait_time)
        
        return 0

class LoginFailedAttemptLimiting(BaseThrottle):

    scope = "email"
    cache_format = "throttle_%(scope)s_%(ident)s"

    def get_cache_key(self, request, view):

        
        #generate cache key based on email address from request data
        email = None
        email = request.data.get("email")
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}#<--both same --> f"throttle_email_{email}"  

        
    def allow_request(self, request, view):

        self.key = self.get_cache_key(request,view)
        if self.key is None:
            return True
        
        min_attempt = 3
       
        throttle_history = cache.get(self.key,{"attempt":0, "next_allowed_time":0,"last_request_time":0})
        # current_time = time.time()

        if  min_attempt > throttle_history["attempt"] +1:
            remaining_attempt = min_attempt - (throttle_history["attempt"]+1)
            throttle_history["attempt"] +=1 
            print("remain " , remaining_attempt)
            cache.set(self.key , throttle_history, None)
            return True     
        
        return False
        

        


      
