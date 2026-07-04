from django.contrib import admin
from .models import ChatSession, ChatMessage

# Inline dikhane ke liye taaki Session ke andar hi saari chat dikh jaye
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'text', 'timestamp') # Chat edit na ho paye Admin se
    can_delete = False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'created_at')
    list_filter = ('company', 'created_at')
    search_fields = ('user__first_name', 'user__email', 'company__name')
    inlines = [ChatMessageInline]
    ordering = ('-created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'sender', 'text_snippet', 'timestamp')
    list_filter = ('sender', 'timestamp')
    search_fields = ('text', 'session__user__first_name', 'session__user__email')
    ordering = ('-timestamp',)

    # Message ka chota hissa dikhane ke liye
    def text_snippet(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_snippet.short_description = 'Message'

    def get_user(self, obj):
        return obj.session.user.first_name
    get_user.short_description = 'User'