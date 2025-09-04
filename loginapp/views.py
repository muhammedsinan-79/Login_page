from django.shortcuts import render , redirect
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.core.cache import cache

from .models import RateLimitLog , InvalidCredentialsLog ,LoginCredentialLog
from .throttle import ProgressiveEmailThrottle,LoginFailedAttemptLimiting #IpRateLimiting
from rest_framework.exceptions import Throttled


# Create your views here.

class HomePage(APIView):
    def get(self, request):
        return render(request,'home.html')
        
class SignupPage(APIView):
    def get(self, request):
        return render(request, 'signup.html')
    
    def post(self, request):
        print("incoming data:", request.data)
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('full_name')
        confirm_password = request.data.get('confirm_password')

        if password != confirm_password:
            return render(request, 'signup.html', {
                'error': "Passwords do not match",
                'email': email,
                'full_name': name
            })
        
        if User.objects.filter(username=email).exists():
            return render(request, 'signup.html', {
                'error': "User already exists, please log in.",
                'email': email
            })
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )
        Token.objects.create(user=user)

        return render(request, 'signup.html', {
            'success': "Your account has been created successfully. Please log in."
        })

     
class LoginPage(APIView):

    def handle_exception(self, exc):
        if isinstance(exc, Throttled):
            email = self.request.POST.get("email")
            ip = self.request.META.get('REMOTE_ADDR')
            user_agent = self.request.META.get('HTTP_USER_AGENT')

            print(email,ip,user_agent)

            InvalidCredentialsLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent,
                is_throttled=True                
            )
            return render(self.request, "login.html", {
                "error": "Request Throttled , Please Reset Your Password"#exc.detail --> # this will now show your custom string
            }, status=429)
        return super().handle_exception(exc)
    
    def get(self,request): 
        return render(request , 'login.html')
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        cache_key2 = f"throttleD_email_{email}"

        if cache.get(cache_key2, 0):  # even try with correct password after 3 times fail, get throttle
            raise Throttled()

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return render(request, "login.html", {"error": "User not registered"})

        user = authenticate(username=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)

            cache_key1 = f"throttle_email_{email}"
            cache.delete(cache_key1)  # cache.set in throttle.py
            cache.delete("failed_attempt")  # delete remaining count

            LoginCredentialLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent,
            )
            return render(request, 'login_success.html', {'email': email, 'token': token.key, 'success': 'Login Successful'})

        else:
            throttle = LoginFailedAttemptLimiting()

            if not throttle.allow_request(request, self):
                cache.set(cache_key2, True, None)
                raise Throttled(wait=throttle.wait())

            remaining_attempt = cache.get("failed_attempt", 3)
            remaining_attempt -= 1
            InvalidCredentialsLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent,
            )
            cache.set("failed_attempt", remaining_attempt)

            error_message = f"Invalid Credentials, {remaining_attempt} Attempt(s) Left"
            return render(request, 'login.html', {"error": error_message})


from rest_framework.authtoken.models import Token

class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("User:", request.user)
        print("Token:", request.META.get('HTTP_AUTHORIZATION'))
        print("Is authenticated:", request.user.is_authenticated)

        try:
            token = request.user.auth_token
            token.delete()
            return Response({"message": "Logout successful."})
        except Token.DoesNotExist:
            return Response({"error": "Token not found or already deleted."}, status=400)
        except Exception as e:
            print("Logout failed:", e)
            return Response({"error": "Logout failed."}, status=400)

class ForgotPasswordView(APIView):
    throttle_classes = [ProgressiveEmailThrottle]

    def handle_exception(self, exc):
        if isinstance(exc, Throttled):
            email = self.request.POST.get("email")
            ip = self.request.META.get('REMOTE_ADDR')
            user_agent = self.request.META.get('HTTP_USER_AGENT')

            RateLimitLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent,
                is_throttled=True
            )
            return render(self.request, "forgot_password.html", {
                "error": exc.detail  # display throttling message
            }, status=429)
        return super().handle_exception(exc)
    
    def get(self, request):
        return render(request, 'forgot_password.html')
    
    def post(self, request):
        email = request.data.get('email')
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT') 
        
        Ip_timeout = 600  # 10 min
        ip_limit_count = 5
        ip_key = f"ip_rate_limit:{ip}"

        ip_count = cache.get(ip_key, 0)
        if ip_count >= ip_limit_count:
            RateLimitLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent,
                is_throttled=True
            )
            return render(request, 'forgot_password.html', {
                'error': f"Too many requests from this IP address. Please wait 10 min."
            })

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://20.2.209.183/reset-password/{uid}/{token}/"
            
            send_mail(
                subject="Reset Your Password",
                message=f"Click the link to reset your password: {reset_link}",
                from_email="muhammedsinaan78@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )

            RateLimitLog.objects.create(
                email=email,
                ip_address=ip,
                user_agent=user_agent
            )

            if cache.get(ip_key):
                cache.incr(ip_key)
            else:
                cache.set(ip_key, 1, Ip_timeout)

            # Render forgot_password page with success message
            return render(request, 'login.html', {
                'success': "Password reset email sent successfully."
            })
        
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {
                'error': "User does not exist."
            })
        except Exception as e:
            print(f"Error sending email: {e}")
            return render(request, 'forgot_password.html', {
                'error': "An error occurred. Please try again later."
            })

              
class ResetPasswordView(APIView):
    def get(self, request, uidb64, token):
        # You can add any validation here if needed.
        return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):          
                new_password = request.data.get("password")
                user.set_password(new_password)
                user.save()

                # Clear throttling caches
                cache_key = f"throttle_email_{user.email}"
                cache_key2 = f"throttleD_email_{user.email}"
                cache.delete(cache_key)
                cache.delete(cache_key2)
                cache.delete("failed_attempt") 

                # Render the template with a success message
                return render(request, 'login.html', {
                    'success': "Your password has been changed successfully. Please log in."
                })

            else:
                return render(request, 'reset_password.html', {
                    'error': "Invalid or expired token.",
                    'uidb64': uidb64,
                    'token': token,
                })

        except Exception as e:
            print("Reset error:", e)
            return render(request, 'reset_password.html', {
                'uidb64': uidb64,
                'token': token,
                'error': "Something went wrong."
            })

        


       


         


        
