from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from rest_framework.exceptions import Throttled
import time , logging

logger = logging.getLogger(__name__)
from .logging_config import logger


class ProgressiveEmailThrottle(BaseThrottle):
    scope = "email"
    cache_format = "throttle_%(scope)s_%(ident)s"

    def get_cache_key(self, request, view):
        #generate cache key based on email address from request data
        email = None
        email = request.data.get("email")
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}
    
    def allow_request(self, request, view):

        self.key = self.get_cache_key(request,view)
        if self.key is None:
            return True
        
        rest_time = 3600
        max_attempt = 5
        base_time = 60

        throttle_history = cache.get(
            self.key,{"attempt":0, "next_allowed_time":0,"last_request_time":0}
            )
        current_time = time.time()
        print("current time",current_time)

        #logging

        logger.info(f"[THROTTLE][READ] key={self.key}, history={throttle_history}, now={current_time}")


        if throttle_history["attempt"] >= max_attempt:
            print("throttled for max attempt time",current_time)
            wait_time = (rest_time - (current_time - throttle_history["last_request_time"]))
            print(wait_time)
            logger.warning(f"[THROTTLE][BLOCK] key={self.key}, attempts={throttle_history['attempt']}, wait={wait_time}s")
            raise Throttled(detail="Too many attempts. Please try again after 1 hour.")

        
        if throttle_history["next_allowed_time"] > current_time:
            self.wait_time = throttle_history["next_allowed_time"] -  current_time      
            # print("throttled time , ",current_time)
            # print("throttle history after throttle, ",throttle_history)
            # print(self.wait_time) #remaining time 
            # print(throttle_history["next_allowed_time"]-throttle_history["last_request_time"])  # total wait time
            logger.warning(f"[THROTTLE][WAIT] key={self.key}, must wait={self.wait_time:.1f}s, history={throttle_history}")
            wait_time = int(throttle_history["next_allowed_time"] - current_time)

            minutes, seconds = divmod(wait_time, 60)
            if minutes > 0:
                formatted_time = f"{minutes} min {seconds} seconds"
            else:
                formatted_time = f"{seconds} seconds"
            
            raise Throttled(#wait=wait_time,
                detail=f"Resend Available after {formatted_time} ")

            # return False #self.throttle_failure()
            
        # Calculate wait_time BEFORE incrementing attempt
        wait_time = base_time * (2 ** throttle_history["attempt"])

        attempt_key = f"{self.key}:attempt"
        key = f"{self.key}:attempt"
        if cache.get(key) is None:  #change to cache.incr
            cache.set(key, 0, timeout=3600)  
        throttle_history["attempt"] = cache.incr(key, 1)


        # throttle_history["attempt"] += 1
        throttle_history["last_request_time"] = current_time
        throttle_history["next_allowed_time"] = current_time + wait_time
        
        print("throttle history for allowed request , ",throttle_history)
        ttl = max(wait_time + 5, rest_time)
        cache.set(self.key , throttle_history, timeout=ttl)

        logger.info(f"[THROTTLE][WRITE] key={self.key}, history={throttle_history}, ttl={ttl}s")

        return True  #super().allow_request(request, view)
    
    def wait(self):
        return getattr(self, "wait_time", 60)

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
        
        #rest_time = None
        min_attempt = 3
        # max_attempt = 7
        # base_time = 30

        throttle_history = cache.get(self.key,{"attempt":0, "next_allowed_time":0,"last_request_time":0})
        # current_time = time.time()

        if  min_attempt > throttle_history["attempt"] +1:
            remaining_attempt = min_attempt - (throttle_history["attempt"]+1)
            throttle_history["attempt"] +=1 
            print("remain " , remaining_attempt)
            cache.set(self.key , throttle_history, None)
            return True     
            

        # if throttle_history["attempt"] >= max_attempt:
        #     wait_time = (rest_time - (current_time - throttle_history["last_request_time"]))
        #     print(wait_time)
        #     raise Throttled(detail="Too many attempts. Please try again after 1 hour.")


        # if throttle_history["next_allowed_time"] > current_time:
        #     self.wait_time = throttle_history["next_allowed_time"] -  current_time

        #     print(self.wait_time) #remaining time 
        #     print(throttle_history["next_allowed_time"]-throttle_history["last_request_time"])  # total wait time

        #     wait_time = int(throttle_history["next_allowed_time"] - current_time)
        #     remaining_attempt = max_attempt - throttle_history["attempt"] 
        #     raise Throttled(wait=wait_time,
        #         detail=f"remaining attempt is {remaining_attempt},")
        
        # throttle_history["attempt"] +=1 
        # throttle_history["last_request_time"] = current_time

        # wait_time = base_time * (2**((throttle_history["attempt"])-min_attempt-1))  # logic  
        # throttle_history["next_allowed_time"] = current_time + wait_time
        # cache.set(self.key , throttle_history, timeout= rest_time)

        return False
        

        


      
