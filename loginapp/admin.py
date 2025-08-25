from django.contrib import admin
from .models import RateLimitLog
from .models import InvalidCredentialsLog

# Register your models here.
@admin.register(RateLimitLog)

class RateLimitLogAdmin(admin.ModelAdmin):
    list_display = ('email','ip_address','timestamp')
    list_filter = ('timestamp',)
    search_fields = ('email', 'ip_address', 'user_agent')



admin.site.register(InvalidCredentialsLog)

