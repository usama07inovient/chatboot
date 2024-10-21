# chatbot/admin.py

from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin
from .models import Chatbot, Form, Question
from django.http import HttpResponseRedirect
import uuid

# Admin for the Chatbot model
# class ChatbotAdmin(admin.ModelAdmin):
#     list_display = ('name', 'user', 'is_active', 'created_at')
#     readonly_fields = ('platform_key_with_actions', 'created_at')

#     def platform_key_with_actions(self, obj):
#         """Only show buttons if this is the change view and the chatbot exists (not on add)."""
#         if obj.pk:
#             regenerate_url = reverse('admin:chatbot_regenerate_key', args=[obj.pk])
#             return format_html(
#                 '''
#                 {} 
#                 <button type="button" style="background-color: #417690; color: white; border: none; padding: 5px 10px; cursor: pointer; transition: 0.3s;" 
#                 onmouseover="this.style.backgroundColor='#365a6f';" onmouseout="this.style.backgroundColor='#417690';"
#                 onclick="navigator.clipboard.writeText('{}');this.innerText='Copied!';setTimeout(() => this.innerText='Copy', 2000);">Copy</button>
                
#                 <button type="button" style="background-color: #5fa225; color: white; border: none; padding: 5px 10px; cursor: pointer; transition: 0.3s;" 
#                 onmouseover="this.style.backgroundColor='#4d821c';" onmouseout="this.style.backgroundColor='#5fa225';"
#                 onclick="if (confirm('Are you sure you want to regenerate the platform key? This will affect your integration iframe.')) {{ window.location.href='{}'; }}">Regenerate</button>
#                 ''',
#                 obj.platform_key, obj.platform_key, regenerate_url
#             )
#         return "N/A"

#     platform_key_with_actions.short_description = "Platform Key & Actions"

#     def get_urls(self):
#         from django.urls import path
#         urls = super().get_urls()
#         custom_urls = [
#             path('<int:chatbot_id>/regenerate-key/', self.admin_site.admin_view(self.regenerate_platform_key), name='chatbot_regenerate_key'),
#         ]
#         return custom_urls + urls

#     def regenerate_platform_key(self, request, chatbot_id):
#         """Regenerate the platform key for the Chatbot and redirect back."""
#         chatbot = self.get_object(request, chatbot_id)
#         if chatbot:
#             chatbot.platform_key = uuid.uuid4()  # Generate a new key
#             chatbot.save()
#             self.message_user(request, f'Platform key for {chatbot.name} regenerated successfully.')
#         return HttpResponseRedirect(reverse('admin:chatbot_chatbot_change', args=[chatbot_id]))


# chatbot/admin.py

# chatbot/admin.py

from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin
from .models import Chatbot, Form, Question
from django.http import HttpResponseRedirect
import uuid

class ChatbotAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'created_at')
    readonly_fields = ('platform_key_with_actions', 'created_at')
    
    def platform_key_with_actions(self, obj):
        """Show platform key with copy and regenerate buttons."""
        if obj.pk:
            regenerate_url = reverse('admin:chatbot_regenerate_key', args=[obj.pk])
            return format_html(
                '''
                {} 
                <button type="button" onclick="navigator.clipboard.writeText('{}');this.innerText='Copied!';setTimeout(() => this.innerText='Copy', 2000);">Copy</button>
                <button type="button" onclick="if(confirm('Regenerate?')) {{ window.location.href='{}'; }}">Regenerate</button>
                ''',
                obj.platform_key, obj.platform_key, regenerate_url
            )
        return "N/A"

    platform_key_with_actions.short_description = "Platform Key & Actions"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Disable DataPipeline dropdown for non-superusers."""
        if db_field.name == "form" and not request.user.is_superuser:
            kwargs["disabled"] = True  # Disable for non-superusers
        if db_field.name == "data_pipeline" and not request.user.is_superuser:
            kwargs["disabled"] = True  # Disable for non-superusers
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Override permission methods
    def has_view_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.view_own_chatbot') or request.user.is_superuser
        return obj.user == request.user and request.user.has_perm('chatbot.view_own_chatbot') or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.has_perm('chatbot.create_own_chatbot') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.update_own_chatbot') or request.user.is_superuser
        return obj.user == request.user and request.user.has_perm('chatbot.update_own_chatbot') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.delete_own_chatbot') or request.user.is_superuser
        return obj.user == request.user and request.user.has_perm('chatbot.delete_own_chatbot') or request.user.is_superuser

    def save_model(self, request, obj, form, change):
        # Ensure that non-superusers can only create chatbots for themselves
        if not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:chatbot_id>/regenerate-key/', self.admin_site.admin_view(self.regenerate_platform_key), name='chatbot_regenerate_key'),
        ]
        return custom_urls + urls

    def regenerate_platform_key(self, request, chatbot_id):
        chatbot = self.get_object(request, chatbot_id)
        if chatbot and (chatbot.user == request.user or request.user.is_superuser):
            chatbot.platform_key = uuid.uuid4()
            chatbot.save()
            self.message_user(request, f'Platform key for {chatbot.name} regenerated successfully.')
        return HttpResponseRedirect(reverse('admin:chatbot_chatbot_change', args=[chatbot_id]))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


# Inline for Question (displayed as part of the Form admin)
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


# Admin for the Form model, including Questions and their Answers
class FormAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('title',)

    fieldsets = (
        (None, {
            'fields': ('title', 'created_at'),
        }),
    )

    def has_add_permission(self, request):
        return request.user.has_perm('chatbot.add_own_form') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('chatbot.update_own_form') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('chatbot.delete_own_form') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('chatbot.view_own_form') or request.user.is_superuser


# Register the models with the custom admin configurations
admin.site.register(Form, FormAdmin)
admin.site.register(Chatbot, ChatbotAdmin)
