from django.contrib import admin
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import DataPipeline, DataSource
from chatbot.models import Chatbot
# Custom form for DataPipeline to handle URL change validation
class DataPipelineAdminForm(forms.ModelForm):
    class Meta:
        model = DataPipeline
        fields = '__all__'

    def clean_url(self):
        if self.instance.pk:  # Only validate if the instance exists
            old_instance = DataPipeline.objects.get(pk=self.instance.pk)
            # Check if the URL is being changed while status is 'pending'
            if self.instance.status == 'pending' and old_instance.url != self.cleaned_data['url']:
                raise ValidationError("You cannot change the URL when the Data Pipeline status is 'pending'.")
        return self.cleaned_data['url']

# Custom formset to handle the status check during save
class DataSourceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        
        # Access the related instance (DataPipeline)
        if self.instance.status == 'pending':
            raise ValidationError("You cannot add, modify, or delete Data Sources when the Data Pipeline status is 'pending'.")

    def save_new(self, form, commit=True):
        # Prevent saving if the DataPipeline status is 'pending'
        if self.instance.status == 'pending':
            messages.error(self.request, "You cannot add Data Sources when the Data Pipeline status is 'pending'.")
            return None
        return super().save_new(form, commit=commit)

    def save_existing(self, form, instance, commit=True):
        # Prevent saving if the DataPipeline status is 'pending'
        if self.instance.status == 'pending':
            messages.error(self.request, "You cannot modify Data Sources when the Data Pipeline status is 'pending'.")
            return None
        return super().save_existing(form, instance, commit=commit)

# Inline for DataSource, allowing multiple file uploads for a single DataPipeline
class DataSourceInline(admin.TabularInline):
    model = DataSource
    formset = DataSourceInlineFormSet  # Use the custom formset
    extra = 1  # Show one extra empty file field by default
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    verbose_name_plural = 'Data Sources'

    def has_add_permission(self, request, obj=None):
        # Check the user's permission
        return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Check the user's permission and whether they own the chatbot
        if obj is None:
            return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Check the user's permission and whether they own the chatbot
        if obj is None:
            return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        # Check the user's permission and whether they own the chatbot
        if obj is None:
            return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

    def get_formset(self, request, obj=None, **kwargs):
        # Pass the request to the formset so we can use messages in validation
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request  # Attach request to formset for messaging
        return formset


# Admin class for DataPipeline using the custom form
class DataPipelineAdmin(admin.ModelAdmin):
    form = DataPipelineAdminForm  # Use the custom form here
    inlines = [DataSourceInline]
    list_display = ('name', 'chatbot', 'url', 'created_at', "status","uuid")
    readonly_fields = ('created_at', "updated_at","uuid")
    search_fields = ('name', 'url')
    fieldsets = (
        (None, {
            'fields': ('name', 'chatbot', 'url', 'created_at', "status", "updated_at","uuid"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = DataPipeline.objects.get(pk=obj.pk)
            if obj.status == 'pending' and old_obj.url != obj.url:
                # Use Django's messages framework to display the error on the admin page
                self.message_user(
                    request,
                    _("You cannot change the URL when the Data Pipeline status is 'pending'."),
                    level=messages.ERROR
                )
                return  # Prevent the save from proceeding
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter data pipelines based on the chatbots owned by the current user
        return qs.filter(chatbot__users=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if hasattr(form, 'base_fields') and 'chatbot' in form.base_fields:
            if not request.user.is_superuser:
                form.base_fields['chatbot'].queryset = Chatbot.objects.filter(users=request.user)
        return form

    def has_add_permission(self, request):
        return request.user.has_perm('data_pipeline.add_own_pipeline') or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
        return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser


# Register the DataPipeline model
admin.site.register(DataPipeline, DataPipelineAdmin)

# admin.site.register(DataSource)


