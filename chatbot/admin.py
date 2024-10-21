from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin
from .models import Chatbot, Form, DataPipeline, Question
from django.http import HttpResponseRedirect
import uuid
from django import forms
from django.conf import settings  # Import to access the server domain constant

class FormInline(admin.TabularInline):
    model = Form
    extra = 0
    readonly_fields = ('title', 'created_at', 'form_view_link')
    can_delete = False
    request = None  # Placeholder for the request object

    def has_add_permission(self, request, obj=None):
        return False

    def form_view_link(self, obj):
        if obj:
            view_url = reverse('admin:chatbot_form_change', args=[obj.pk])
            edit_url = reverse('admin:chatbot_form_change', args=[obj.pk])
            
            # Only show the "Edit" button if the user has change permission
            edit_button = format_html('<a href="{}" class="button">Edit</a>', edit_url) if self.has_change_permission(self.request, obj) else ""
            
            # Show the "View" button if the user has view permission
            view_button = format_html('<a href="{}" class="button">View</a>', view_url) if self.has_view_permission(self.request, obj) else ""

            return format_html('{} {}', edit_button, view_button)
        return 'No form'

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('chatbot.update_own_form') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('chatbot.delete_own_form') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('chatbot.view_own_form') or request.user.is_superuser

    fields = ['title', 'created_at', 'form_view_link']
    form_view_link.short_description = "Actions"


class DataPipelineInline(admin.TabularInline):
    model = DataPipeline
    extra = 0
    readonly_fields = ('name', 'status', 'created_at', 'pipeline_view_link')
    can_delete = False
    request = None  # Placeholder for the request object

    def has_add_permission(self, request, obj=None):
        return False

    def pipeline_view_link(self, obj):
        if obj:
            view_url = reverse('admin:data_pipeline_datapipeline_change', args=[obj.pk])
            edit_url = reverse('admin:data_pipeline_datapipeline_change', args=[obj.pk])
            
            # Only show the "Edit" button if the user has change permission
            edit_button = format_html('<a href="{}" class="button">Edit</a>', edit_url) if self.has_change_permission(self.request, obj) else ""
            
            # Show the "View" button if the user has view permission
            view_button = format_html('<a href="{}" class="button">View</a>', view_url) if self.has_view_permission(self.request, obj) else ""

            return format_html('{} {}', edit_button, view_button)
        return 'No pipeline'

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

    fields = ['name', 'status', 'created_at', 'pipeline_view_link']
    pipeline_view_link.short_description = "Actions"

class ChatbotAdminForm(forms.ModelForm):
    class Meta:
        model = Chatbot
        fields = '__all__'
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'id': 'is-active-toggle', 'class': 'toggle-checkbox'}),
            'save_user_chatsession': forms.CheckboxInput(attrs={'id': 'save-session-toggle', 'class': 'toggle-checkbox'}),
        }

class ChatbotAdmin(admin.ModelAdmin):
    form = ChatbotAdminForm  # Attach the custom form

    list_display = ('name', 'is_active', 'created_at', 'list_users')  # Add the 'list_users' method to list_display
    # readonly_fields = ('platform_key_with_actions', 'created_at', 'chatbot_iframe', 'iframe_code')  # Add the iframe field here
    # readonly_fields = ('platform_key_with_actions', 'created_at', 'iframe_code')  # Add the iframe field here

    inlines = [FormInline, DataPipelineInline]  # Attach both Form and DataPipeline inlines
    change_form_template = 'admin/chatbot_change_form.html'
    add_form_template = 'admin/chatbot_change_form.html'
    filter_horizontal = ['users']

    def list_users(self, obj):
        """
        Custom method to list the names of users attached to the chatbot.
        """
        return ", ".join([user.username for user in obj.users.all()])

    list_users.short_description = "Users Attached"  # Set a descriptive label for the column

    # def chatbot_iframe(self, obj):
    #     """
    #     Custom method to generate an iframe for the chatbot, dynamically replacing the platform key and user info.
    #     """
    #     if obj.pk:
    #         # Get the server domain from settings.py
    #         server_domain = settings.CHATBOT_SERVER_DOMAIN

    #         # Ensure there are users to pull the email and username from
    #         if obj.users.exists():
    #             user = obj.users.first()  # Just taking the first user, modify as needed
    #             iframe_src = f"{server_domain}/chatbot/chat/{obj.platform_key}/?email=usama@usama.com&username=usama"
    #             # iframe_src = f"{server_domain}/chatbot/chat/{obj.platform_key}/?email={user.email}&username={user.username}"
    #             return format_html(
    #                 '''
    #                 <iframe id="responsive-chatbot-iframe" class="responsive-chatbot" src="{}" style="height: unset; min-width: 400px; min-height: 600px;"></iframe>
    #                 ''',
    #                 iframe_src
    #             )
    #     return "No iframe available."

    # chatbot_iframe.short_description = "Chatbot Iframe"

    def iframe_code(self, obj):
        """
        Method to return the iframe HTML code inside a disabled <textarea> with a 'Copy' button.
        """
        if obj.pk:
            server_domain = settings.CHATBOT_SERVER_DOMAIN

            if obj.users.exists():
                user = obj.users.first()  # Take the first user as an example
                iframe_code = (
                    f'<iframe id="responsive-chatbot-iframe" class="responsive-chatbot" '
                    f'src="{server_domain}/chatbot/chat/{obj.platform_key}/?email=<user-email>&username=<username>" '
                    f'style="height: unset; min-width: 400px; min-height: 600px;"></iframe>'
                )
                # Return the iframe code inside a disabled textarea and a copy button
                return format_html(
                    '''
                    <textarea id="iframeCode" style="width: 100%;" rows="4" readonly>{}</textarea>
                    <button type="button" onclick="copyToClipboard()">Copy</button>
                    <script>
                        function copyToClipboard() {{
                            var copyText = document.getElementById("iframeCode");
                            copyText.select();
                            document.execCommand("copy");
                            alert("Copied the iframe code!");
                        }}
                    </script>
                    ''',
                    iframe_code
                )
        return "No iframe code available."

    iframe_code.short_description = "Iframe Code (Copy & Paste)"

    def platform_key_with_actions(self, obj):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(users=request.user)

    def get_form(self, request, obj=None, **kwargs):
        # self.readonly_fields = ('platform_key_with_actions', 'created_at', 'chatbot_iframe', 'iframe_code')
        self.readonly_fields = ('platform_key_with_actions', 'created_at', 'iframe_code')

        if not request.user.has_perm('chatbot.activate_chatbot'):
            self.readonly_fields += ('is_active',)

        if not request.user.has_perm('chatbot.modify_chat_save_session'):
            self.readonly_fields += ('save_user_chatsession',)

        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            if 'users' in form.base_fields:
                form.base_fields.pop('users')

        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not request.user.is_superuser:
            if request.user not in obj.users.all():
                obj.users.add(request.user)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:chatbot_id>/regenerate-key/', self.admin_site.admin_view(self.regenerate_platform_key), name='chatbot_regenerate_key'),
        ]
        return custom_urls + urls

    def regenerate_platform_key(self, request, chatbot_id):
        chatbot = self.get_object(request, chatbot_id)
        if chatbot and (request.user in chatbot.users.all() or request.user.is_superuser):
            chatbot.platform_key = uuid.uuid4()
            chatbot.save()
            self.message_user(request, f'Platform key for {chatbot.name} regenerated successfully.')
        return HttpResponseRedirect(reverse('admin:chatbot_chatbot_change', args=[chatbot_id]))

    def get_inline_instances(self, request, obj=None):
        """
        Pass the request object to the inline instances.
        """
        inline_instances = super().get_inline_instances(request, obj)
        for inline in inline_instances:
            inline.request = request  # Pass the request object to the inlines
        return inline_instances

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        chatbot = self.get_object(request, object_id)

        ## Safely check if the chatbot has a form
        if not getattr(chatbot, 'form', None):  # This will safely return None if the form doesn't exist
            if request.user.has_perm('chatbot.add_own_form') or request.user.is_superuser:
                add_form_url = reverse('admin:chatbot_form_add') + f'?chatbot={object_id}'
                extra_context['add_form_button'] = format_html('<a class="button" href="{}">Add Form</a>', add_form_url)

        if not getattr(chatbot, 'data_pipeline', None):  # This will safely return None if the data pipeline doesn't exist
            if request.user.has_perm('data_pipeline.add_own_pipeline') or request.user.is_superuser:
                add_pipeline_url = reverse('admin:data_pipeline_datapipeline_add') + f'?chatbot={object_id}'
                extra_context['add_pipeline_button'] = format_html('<a class="button" href="{}">Add Data Pipeline</a>', add_pipeline_url)

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def has_add_permission(self, request):
        return request.user.has_perm('chatbot.create_own_chatbot') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.update_own_chatbot') or request.user.is_superuser
        return request.user in obj.users.all() and request.user.has_perm('chatbot.update_own_chatbot') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.delete_own_chatbot') or request.user.is_superuser
        return request.user in obj.users.all() and request.user.has_perm('chatbot.delete_own_chatbot') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.view_own_chatbot') or request.user.is_superuser
        return request.user in obj.users.all() and request.user.has_perm('chatbot.view_own_chatbot') or request.user.is_superuser


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

    def has_add_permission(self, request, obj=None):
        """
        Control if the 'Add Question' option should appear based on user permissions.
        """
        # return request.user.has_perm('chatbot.add_own_form') or request.user.is_superuser
        return request.user.has_perm('chatbot.update_own_form') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """
        Control if the 'Edit Question' option should appear based on user permissions.
        """
        return request.user.has_perm('chatbot.update_own_form') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """
        Control if the 'Delete Question' option should appear based on user permissions.
        """
        return request.user.has_perm('chatbot.delete_own_form') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """
        Control if the 'View Question' option should appear based on user permissions.
        """

        # print(request.user.has_perm('chatbot.view_own_form'))
        return request.user.has_perm('chatbot.view_own_form') or request.user.is_superuser

class FormAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

    list_display = ('title', 'chatbot', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('title',)

    fieldsets = (
        (None, {
            'fields': ('title', 'chatbot', 'created_at', "whatsapp_link"),
        }),
    )

    def get_queryset(self, request):
        """
        Show all forms for superusers and only user-related forms for non-superusers.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter forms based on the chatbots owned by the current user
        return qs.filter(chatbot__users=request.user)

    def get_form(self, request, obj=None, **kwargs):
        """
        Customize the form to only show chatbots related to the current user in the chatbot field.
        """
        form = super().get_form(request, obj, **kwargs)
        # Check if base_fields exists and the form is not in read-only mode
        if hasattr(form, 'base_fields') and 'chatbot' in form.base_fields:
            if not request.user.is_superuser:
                # Limit the chatbot choices to the current user's chatbots
                form.base_fields['chatbot'].queryset = Chatbot.objects.filter(users=request.user)
        return form

    def save_model(self, request, obj, form, change):
        """
        Ensure that the form is correctly linked to a chatbot owned by the user.
        """
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('chatbot.add_own_form') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.update_own_form') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('chatbot.update_own_form') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.delete_own_form') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('chatbot.delete_own_form') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('chatbot.view_own_form') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('chatbot.view_own_form') or request.user.is_superuser

# Register the models with the custom admin configurations
admin.site.register(Form, FormAdmin)
admin.site.register(Chatbot, ChatbotAdmin)
