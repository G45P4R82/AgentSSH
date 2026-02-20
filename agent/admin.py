from django.contrib import admin
from .models import RemoteHost, AgentTask


@admin.register(RemoteHost)
class RemoteHostAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostname', 'username', 'created_at')
    search_fields = ('name', 'hostname', 'username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = ('host', 'prompt_short', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'host')
    search_fields = ('prompt', 'generated_command', 'output')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def prompt_short(self, obj):
        return obj.prompt[:50] + '...' if len(obj.prompt) > 50 else obj.prompt
    prompt_short.short_description = 'Prompt'
