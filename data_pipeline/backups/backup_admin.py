# from django.contrib import admin
# from .models import DataPipeline, DataSource
# from django.contrib import admin
# from .models import DataPipeline
# from chatbot.models import Chatbot
# from django import forms
# from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.contrib import messages

# class DataSourceAdminForm(forms.ModelForm):
#     class Meta:
#         model = DataSource
#         fields = ['file', 'data_pipeline']

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Add the `accept` attribute to restrict file types (pdf, doc, docx, csv)
#         self.fields['file'].widget.attrs.update({'accept': settings.ALLOWED_FILE_TYPES})

# # Inline for DataSource, allowing multiple file uploads for a single DataPipeline
# # class DataSourceInline(admin.TabularInline):
# #     model = DataSource
# #     extra = 1  # Show one extra empty file field by default
# #     fields = ('file', 'uploaded_at')
# #     readonly_fields = ('uploaded_at',)
# #     verbose_name_plural = 'Data Sources'
# #     form = DataSourceAdminForm  # Attach the custom form to inline

# #     def has_add_permission(self, request,obj=None):
# #         return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_change_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_delete_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

# #     def has_view_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser





# from django.core.exceptions import ValidationError

# # Inline for DataSource, allowing multiple file uploads for a single DataPipeline
# class DataSourceInline(admin.TabularInline):
#     model = DataSource
#     extra = 1  # Show one extra empty file field by default
#     fields = ('file', 'uploaded_at')
#     readonly_fields = ('uploaded_at',)
#     verbose_name_plural = 'Data Sources'
#     form = DataSourceAdminForm  # Attach the custom form to inline

#     def has_add_permission(self, request, obj=None):
#         # Check if the DataPipeline status is 'pending'
#         if obj and obj.status == 'pending':
#             return False  # Disable add permission when status is pending
#         return super().has_add_permission(request, obj)

#     def has_change_permission(self, request, obj=None):
#         # Check if the DataPipeline status is 'pending'
#         if obj and obj.status == 'pending':
#             return False  # Disable change permission when status is pending
#         return super().has_change_permission(request, obj)

#     def has_delete_permission(self, request, obj=None):
#         # Check if the DataPipeline status is 'pending'
#         if obj and obj.status == 'pending':
#             return False  # Disable delete permission when status is pending
#         return super().has_delete_permission(request, obj)

#     def save_model(self, request, obj, form, change):
#         # Check if the related DataPipeline status is 'pending'
#         if obj.data_pipeline.status == 'pending':
#             raise ValidationError("You cannot add, update, or delete Data Sources when the Data Pipeline status is 'pending'.")
#         super().save_model(request, obj, form, change)

#     def delete_model(self, request, obj):
#         # Check if the related DataPipeline status is 'pending'
#         if obj.data_pipeline.status == 'pending':
#             raise ValidationError("You cannot delete Data Sources when the Data Pipeline status is 'pending'.")
#         super().delete_model(request, obj)

# from django import forms
# from .models import DataPipeline
# from django.core.exceptions import ValidationError

# class DataPipelineAdminForm(forms.ModelForm):
#     class Meta:
#         model = DataPipeline
#         fields = '__all__'

#     # def clean(self):
#     #     cleaned_data = super().clean()
#     #     status = cleaned_data.get('status')
#     #     if status == 'pending':
#     #         raise ValidationError(f"The pipeline '{cleaned_data.get('name')}' is on training and cannot be updated.")
#     #     return cleaned_data

#     def clean_url(self):
#         # Only validate if the instance already exists (update)
#         if self.instance.pk:
#             old_instance = DataPipeline.objects.get(pk=self.instance.pk)
#             # Check if the URL is being changed while status is 'pending'
#             if self.instance.status == 'pending' and old_instance.url != self.cleaned_data['url']:
#                 raise ValidationError("You cannot change the URL when the Data Pipeline status is 'pending'.")
#         return self.cleaned_data['url']
    
# class DataPipelineAdmin(admin.ModelAdmin):
#     inlines = [DataSourceInline]
#     # Use the custom form
#     # form = DataPipelineAdminForm
#     # Include the `url` field in list_display
#     list_display = ('name', 'chatbot', 'url', 'created_at', "status")
    
#     # Include the `url` field in readonly_fields, if you don't want it to be editable after creation
#     readonly_fields = ('created_at', "updated_at")
    
#     # Add the `url` field to the search_fields
#     search_fields = ('name', 'url')

#     # Include the `url` field in fieldsets
#     fieldsets = (
#         (None, {
#             'fields': ('name', 'chatbot', 'url', 'created_at',"status","updated_at"),
#         }),
#     )

#     def get_queryset(self, request):
#         """
#         Show all pipelines for superusers and only user-related pipelines for non-superusers.
#         """
#         qs = super().get_queryset(request)
#         if request.user.is_superuser:
#             return qs
#         # Filter data pipelines based on the chatbots owned by the current user
#         return qs.filter(chatbot__users=request.user)

#     def get_form(self, request, obj=None, **kwargs):
#         """
#         Customize the form to only show chatbots related to the current user in the chatbot field.
#         """
#         form = super().get_form(request, obj, **kwargs)
#         # Check if base_fields exists and the form is not in read-only mode
#         if hasattr(form, 'base_fields') and 'chatbot' in form.base_fields:
#             if not request.user.is_superuser:
#                 # Limit the chatbot choices to the current user's chatbots
#                 form.base_fields['chatbot'].queryset = Chatbot.objects.filter(users=request.user)
#         return form

#     def save_model(self, request, obj, form, change):
#         """
#         Ensure the chatbot is correctly linked when saving a new data pipeline.
#         """
#         super().save_model(request, obj, form, change)

#     # def save_model(self, request, obj, form, change):
#     #     # Check if the status is 'pending' and the URL has been modified
#     #     if change:
#     #         old_obj = DataPipeline.objects.get(pk=obj.pk)
#     #         if obj.status == 'pending' and old_obj.url != obj.url:
#     #             # Use Django's messages framework to display the error on the admin page
#     #             self.message_user(
#     #                 request,
#     #                 ("You cannot change the URL when the Data Pipeline status is 'pending'."),
#     #                 level=messages.ERROR
#     #             )
#     #             # Prevent the save from proceeding
#     #             return
#     #     super().save_model(request, obj, form, change)

#     def has_add_permission(self, request):
#         return request.user.has_perm('data_pipeline.add_own_pipeline') or request.user.is_superuser

#     def has_change_permission(self, request, obj=None):
#         if obj is None:
#             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
#         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

#     def has_delete_permission(self, request, obj=None):
#         if obj is None:
#             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
#         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
    

#     def has_view_permission(self, request, obj=None):
#         if obj is None:
#             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
#         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

# # Register the DataPipeline model
# admin.site.register(DataPipeline, DataPipelineAdmin)







# # # Admin for DataPipeline, including DataSource inline
# # class DataPipelineAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'status', 'url', 'created_at')
# #     readonly_fields = ('created_at',)
# #     inlines = [DataSourceInline]  # Include the DataSource inline to manage files
# #     search_fields = ('name',)

# #     # Fields to be displayed when adding/editing DataPipeline
# #     fieldsets = (
# #         (None, {
# #             'fields': ('name', 'url', 'status', 'created_at'),
# #         }),
# #     )

# #     def get_fieldsets(self, request, obj=None):
# #         if not obj:  # When adding a new pipeline
# #             return (
# #                 (None, {
# #                     'fields': ('name', 'url', 'status'),
# #                 }),
# #             )
# #         return super().get_fieldsets(request, obj)

# #     # Custom permissions handling for view, add, change, and delete
# #     def has_view_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
# #         return obj.user == request.user and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

# #     def has_add_permission(self, request):
# #         return request.user.has_perm('data_pipeline.add_own_pipeline') or request.user.is_superuser

# #     def has_change_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
# #         return obj.user == request.user and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_delete_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
# #         return obj.user == request.user and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

# # # Register the models with the custom admin configurations
# # admin.site.register(DataPipeline, DataPipelineAdmin)


# # from django.contrib import admin
# # from .models import DataPipeline
# # from chatbot.models import Chatbot

# # class DataPipelineAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'created_at', 'get_related_chatbot')
# #     readonly_fields = ('created_at',)
# #     search_fields = ('name',)

# #     fieldsets = (
# #         (None, {
# #             'fields': ('name', 'created_at'),
# #         }),
# #     )

# #     def get_related_chatbot(self, obj):
# #         """
# #         Custom method to display the related chatbot.
# #         This uses reverse lookup to access the chatbot associated with the data pipeline.
# #         """
# #         chatbot = Chatbot.objects.filter(data_pipeline=obj).first()  # Reverse lookup from Chatbot
# #         if chatbot:
# #             return chatbot.name
# #         return '-'

# #     get_related_chatbot.short_description = 'Chatbot'

# #     def get_queryset(self, request):
# #         """
# #         Show all pipelines for superusers and only user-related pipelines for non-superusers.
# #         """
# #         qs = super().get_queryset(request)
# #         if request.user.is_superuser:
# #             return qs
# #         # Get all chatbots owned by the current user and filter pipelines based on those chatbots
# #         user_chatbots = Chatbot.objects.filter(users=request.user)
# #         return qs.filter(chatbot__in=user_chatbots)

# #     def get_form(self, request, obj=None, **kwargs):
# #         """
# #         Customize the form to pre-select the chatbot based on the GET parameter or the current user.
# #         Disable the chatbot field for non-superusers.
# #         """
# #         form = super().get_form(request, obj, **kwargs)
# #         chatbot_id = request.GET.get('chatbot')
# #         if chatbot_id:
# #             try:
# #                 chatbot = Chatbot.objects.get(pk=chatbot_id)
# #                 # Prefill and lock the field if a chatbot is selected via the URL
# #                 form.base_fields['name'].initial = f"Pipeline for {chatbot.name}"
# #             except Chatbot.DoesNotExist:
# #                 pass
# #         return form

# #     def save_model(self, request, obj, form, change):
# #         """
# #         Ensure that the chatbot is linked when saving the data pipeline.
# #         """
# #         chatbot_id = request.GET.get('chatbot')
# #         if chatbot_id:
# #             try:
# #                 chatbot = Chatbot.objects.get(pk=chatbot_id)
# #                 chatbot.data_pipeline = obj  # Link the chatbot to the data pipeline
# #                 chatbot.save()
# #             except Chatbot.DoesNotExist:
# #                 self.message_user(request, "Chatbot does not exist.", level='error')
# #                 return
# #         super().save_model(request, obj, form, change)

# #     def has_add_permission(self, request):
# #         return request.user.has_perm('data_pipeline.add_own_pipeline') or request.user.is_superuser

# #     def has_change_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_delete_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

# #     def has_view_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

# # # Register the admin
# # admin.site.register(DataPipeline, DataPipelineAdmin)




# # from django import forms
# # from django.contrib import admin
# # from .models import DataPipeline
# # from chatbot.models import Chatbot

# # class DataPipelineForm(forms.ModelForm):
# #     """
# #     Custom form to add a chatbot selection dropdown to the DataPipeline admin.
# #     """
# #     chatbot = forms.ModelChoiceField(
# #         queryset=Chatbot.objects.filter(data_pipeline__isnull=True),  # Only show chatbots that don't have a pipeline yet
# #         required=True,
# #         label="Chatbot"
# #     )

# #     class Meta:
# #         model = DataPipeline
# #         fields = '__all__'

# # class DataPipelineAdmin(admin.ModelAdmin):
# #     form = DataPipelineForm
# #     list_display = ('name', 'created_at', 'get_related_chatbot')
# #     readonly_fields = ('created_at',)
# #     search_fields = ('name',)

# #     fieldsets = (
# #         (None, {
# #             'fields': ('name', 'chatbot', 'created_at'),
# #         }),
# #     )

# #     def get_related_chatbot(self, obj):
# #         """
# #         Custom method to display the related chatbot.
# #         This uses reverse lookup to access the chatbot associated with the data pipeline.
# #         """
# #         chatbot = Chatbot.objects.filter(data_pipeline=obj).first()  # Reverse lookup from Chatbot
# #         if chatbot:
# #             return chatbot.name
# #         return '-'

# #     get_related_chatbot.short_description = 'Chatbot'

# #     def get_form(self, request, obj=None, **kwargs):
# #         """
# #         Customize the form to pre-select the chatbot for non-superusers.
# #         Also, prefill the chatbot field if it already has one.
# #         """
# #         form = super().get_form(request, obj, **kwargs)

# #         # If editing an existing DataPipeline, pre-select the chatbot
# #         if obj and obj.pk:
# #             chatbot = Chatbot.objects.filter(data_pipeline=obj).first()
# #             if chatbot:
# #                 form.base_fields['chatbot'].initial = chatbot

# #         if not request.user.is_superuser:
# #             # Limit chatbot choices to the current user's chatbots that don't already have a pipeline
# #             form.base_fields['chatbot'].queryset = Chatbot.objects.filter(users=request.user, data_pipeline__isnull=True) | Chatbot.objects.filter(data_pipeline=obj)
        
# #         return form


# #     def save_model(self, request, obj, form, change):
# #         """
# #         Ensure that the selected chatbot is linked to the data pipeline after the pipeline is saved.
# #         """
# #         # First, save the DataPipeline object
# #         super().save_model(request, obj, form, change)

# #         # After the DataPipeline object is saved, link it to the chatbot
# #         chatbot = form.cleaned_data.get('chatbot')
# #         if chatbot:
# #             chatbot.data_pipeline = obj  # Link the selected chatbot to the saved data pipeline
# #             chatbot.save()  # Save the chatbot after linking it


# #     def get_queryset(self, request):
# #         """
# #         Show all pipelines for superusers and only user-related pipelines for non-superusers.
# #         """
# #         qs = super().get_queryset(request)
# #         if request.user.is_superuser:
# #             return qs
# #         # Get all chatbots owned by the current user and filter pipelines based on those chatbots
# #         user_chatbots = Chatbot.objects.filter(users=request.user)
# #         return qs.filter(chatbot__in=user_chatbots)

# #     def has_add_permission(self, request):
# #         return request.user.has_perm('data_pipeline.add_own_pipeline') or request.user.is_superuser

# #     def has_change_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
# #         chatbot = Chatbot.objects.filter(data_pipeline=obj).first()
# #         return chatbot and request.user in chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_delete_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
# #         chatbot = Chatbot.objects.filter(data_pipeline=obj).first()
# #         return chatbot and request.user in chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

# #     def has_view_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
# #         chatbot = Chatbot.objects.filter(data_pipeline=obj).first()
# #         return chatbot and request.user in chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

# # # Register the admin
# # admin.site.register(DataPipeline, DataPipelineAdmin)







# # from django.contrib import admin
# # from .models import DataPipeline, DataSource
# # from chatbot.models import Chatbot
# # from django import forms
# # from django.conf import settings
# # from django.core.exceptions import ValidationError

# # class DataSourceAdminForm(forms.ModelForm):
# #     class Meta:
# #         model = DataSource
# #         fields = ['file', 'data_pipeline']

# #     def __init__(self, *args, **kwargs):
# #         super().__init__(*args, **kwargs)
# #         # Add the `accept` attribute to restrict file types (pdf, doc, docx, csv)
# #         self.fields['file'].widget.attrs.update({'accept': settings.ALLOWED_FILE_TYPES})

# # # Inline for DataSource, allowing multiple file uploads for a single DataPipeline
# # class DataSourceInline(admin.TabularInline):
# #     model = DataSource
# #     extra = 1  # Show one extra empty file field by default
# #     fields = ('file', 'uploaded_at')
# #     readonly_fields = ('uploaded_at',)
# #     verbose_name_plural = 'Data Sources'
# #     form = DataSourceAdminForm  # Attach the custom form to inline

# #     def has_add_permission(self, request, obj=None):
# #         return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_change_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

# #     def has_delete_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

# #     def has_view_permission(self, request, obj=None):
# #         if obj is None:
# #             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
# #         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

# # class DataPipelineAdminForm(forms.ModelForm):
# #     class Meta:
# #         model = DataPipeline
# #         fields = '__all__'

# #     def clean(self):
# #         cleaned_data = super().clean()
# #         status = cleaned_data.get('status')
# #         if status == 'pending':
# #             raise ValidationError(f"The pipeline '{cleaned_data.get('name')}' is on training and cannot be updated.")
# #         return cleaned_data

# # class DataPipelineAdmin(admin.ModelAdmin):
# #     inlines = [DataSourceInline]
# #     list_display = ('name', 'chatbot', 'url', 'created_at', "status")
# #     readonly_fields = ('created_at', "updated_at")
# #     search_fields = ('name', 'url')

# #     fieldsets = (
# #         (None, {
# #             'fields': ('name', 'chatbot', 'url', 'created_at', "status", "updated_at"),
# #         }),
# #     )

# #     def get_queryset(self, request):
# #         qs = super().get_queryset(request)
# #         if request.user.is_superuser:
# #             return qs
# #         return qs.filter(chatbot__users=request.user)

# #     def get_form(self, request, obj=None, **kwargs):
# #         form = super().get_form(request, obj, **kwargs)
# #         if hasattr(form, 'base_fields') and 'chatbot' in form.base_fields:
# #             if not request.user.is_superuser:
# #                 form.base_fields['chatbot'].queryset = Chatbot.objects.filter(users=request.user)
# #         return form

# #     def save_model(self, request, obj, form, change):
# #         """
# #         Custom save method to handle additions of DataSource instances.
# #         """
# #         super().save_model(request, obj, form, change)  # Save the DataPipeline

# #         # Gather added DataSource changes
# #         added_files = []

# #         # Iterate over the inlines to access their formsets
# #         for inline in self.get_inline_instances(request, obj):
# #             inline_formset = inline.get_formset(request, obj)  # Get the formset
# #             print(inline_formset,"inline_formset")
# #             for inline_form in inline_formset.forms:
# #                 print(inline_form)
# #                 # Check if the inline form has cleaned data and if it's a new instance
# #                 # if inline_form.cleaned_data and inline_form.cleaned_data.get('file') and not inline_form.instance.pk:
# #                 #     added_files.append(inline_form.instance)

# #         # Print out the changes for added files
# #         print("Processing Changes")
# #         print(f"Added Files: {[file.file.name for file in added_files]}")






# #     def delete_model(self, request, obj):
# #         """
# #         Override delete to handle cleanup for DataSources when a DataPipeline is deleted.
# #         """
# #         # Collect and print DataSource deletions
# #         data_sources = DataSource.objects.filter(data_pipeline=obj)
# #         print(f"Deleting DataSources: {[ds.file.name for ds in data_sources]}")

# #         # Delete the DataPipeline
# #         super().delete_model(request, obj)

# # # Register the DataPipeline model
# # admin.site.register(DataPipeline, DataPipelineAdmin)


















# # from django.contrib import admin
# # from .models import DataPipeline, DataSource
# # from chatbot.models import Chatbot
# # from django import forms
# # from django.conf import settings
# # from django.core.exceptions import ValidationError

# # class DataSourceAdminForm(forms.ModelForm):
# #     class Meta:
# #         model = DataSource
# #         fields = ['file', 'data_pipeline']

# #     def __init__(self, *args, **kwargs):
# #         super().__init__(*args, **kwargs)
# #         self.fields['file'].widget.attrs.update({'accept': settings.ALLOWED_FILE_TYPES})

# # class DataSourceInline(admin.TabularInline):
# #     model = DataSource
# #     extra = 1
# #     fields = ('file', 'uploaded_at')
# #     readonly_fields = ('uploaded_at',)
# #     verbose_name_plural = 'Data Sources'
# #     form = DataSourceAdminForm

# # class DataPipelineAdminForm(forms.ModelForm):
# #     class Meta:
# #         model = DataPipeline
# #         fields = '__all__'

# #     def clean(self):
# #         cleaned_data = super().clean()
# #         if cleaned_data.get('status') == 'pending':
# #             raise ValidationError(f"The pipeline '{cleaned_data.get('name')}' is on training and cannot be updated.")
# #         return cleaned_data

# # class DataPipelineAdmin(admin.ModelAdmin):
# #     inlines = [DataSourceInline]
# #     list_display = ('name', 'chatbot', 'url', 'created_at', "status")
# #     readonly_fields = ('created_at', "updated_at")
# #     search_fields = ('name', 'url')

# #     fieldsets = (
# #         (None, {
# #             'fields': ('name', 'chatbot', 'url', 'created_at', "status", "updated_at"),
# #         }),
# #     )

# #     # def save_related(self, request, form, formsets, change):
# #     #     """
# #     #     Override save_related to capture added, updated, and deleted DataSource instances.
# #     #     """
# #     #     super().save_related(request, form, formsets, change)

# #     #     # Initialize lists to track changes
# #     #     added_files = []
# #     #     updated_files = []
# #     #     deleted_files = []

# #     #     # Iterate through the formsets
# #     #     for formset in formsets:
# #     #         print("Formset received:", formset)  # Debug print
# #     #         print(f"Formset type: {type(formset)}")  # Print the type of formset for verification
            
# #     #         # Check if the formset class name is DataSourceFormFormSet
# #     #         if formset.__class__.__name__ == 'DataSourceFormFormSet':
# #     #             print("Processing DataSourceInline formset")
# #     #             for index, data_source_form in enumerate(formset.forms):
# #     #                 print(f"Data Source Form {index} Instance: {data_source_form.instance}")
# #     #                 print("Cleaned Data:", data_source_form.cleaned_data)  # Show cleaned data for debugging
                    
# #     #                 # Check for deletions
# #     #                 if data_source_form.cleaned_data.get('DELETE', False):
# #     #                     deleted_files.append(data_source_form.instance.file.name if data_source_form.instance.file else "No file")
# #     #                     print(f"Data Source Form {index} marked for deletion.")

# #     #                 elif data_source_form.instance.pk:  # Existing DataSource
# #     #                     if data_source_form.has_changed():  # Check if it was updated
# #     #                         updated_files.append(data_source_form.instance.file.name)
# #     #                         print(f"Data Source Form {index} updated to: {data_source_form.instance.file.name}")

# #     #                 else:  # New DataSource
# #     #                     if data_source_form.cleaned_data.get('file'):
# #     #                         added_files.append(data_source_form.cleaned_data['file'].name)
# #     #                         print(f"New DataSource added: {data_source_form.cleaned_data['file'].name}")
# #     #                     else:
# #     #                         print(f"Data Source Form {index} is new but no file uploaded.")

# #     #     # Print the changes processed
# #     #     print("Processing Changes in DataSource:")
# #     #     print(f"Added Files: {added_files}")
# #     #     print(f"Updated Files: {updated_files}")
# #     #     print(f"Deleted Files: {deleted_files}")

# #         # Other methods remain unchanged...

# #     def save_related(self, request, form, formsets, change):
# #         """
# #         Override save_related to capture added, updated, and deleted DataSource instances.
# #         """
# #         super().save_related(request, form, formsets, change)

# #         # Initialize lists to track changes
# #         added_files = []
# #         updated_files = []
# #         deleted_files = []
# #         print(change,"change")
# #         # Iterate through the formsets
# #         for formset in formsets:
# #             print("Formset received:", formset)  # Debug print
# #             print(f"Formset type: {type(formset)}")  # Print the type of formset for verification
            
# #             # Check if the formset class name is DataSourceFormFormSet
# #             if formset.__class__.__name__ == 'DataSourceFormFormSet':
# #                 print("Processing DataSourceInline formset")
# #                 for index, data_source_form in enumerate(formset.forms):
# #                     print(f"Data Source Form {index} Instance: {data_source_form.instance}")
# #                     print(str(data_source_form.instance.file))
# #                     print("Cleaned Data:", data_source_form.cleaned_data)  # Show cleaned data for debugging

# #                     # Get the current file in the database
# #                     current_file = data_source_form.instance.file.name if data_source_form.instance.file else None
# #                     print(data_source_form.instance.pk,"data_source_form.instance.pk")
# #                     # Check for deletions
# #                     if data_source_form.cleaned_data.get('DELETE', False):
# #                         deleted_files.append(current_file if current_file else "No file")
# #                         print(f"Data Source Form {index} marked for deletion.")

# #                     elif data_source_form.instance.pk:  # Existing DataSource
# #                         new_file = data_source_form.cleaned_data.get('file')  # The new file uploaded
# #                         if new_file:  # If a new file is uploaded
# #                             # Mark the old file as deleted if it's being replaced
# #                             updated_files.append(new_file.name)  # Log the new file as updated
# #                             print(f"Data Source Form {index} updated from {current_file} to: {new_file.name}")

# #                         else:
# #                             print(f"Data Source Form {index} has no new file uploaded; current file remains: {current_file}")

# #                     else:  # New DataSource
# #                         if data_source_form.cleaned_data.get('file'):
# #                             added_files.append(data_source_form.cleaned_data['file'].name)
# #                             print(f"New DataSource added: {data_source_form.cleaned_data['file'].name}")
# #                         else:
# #                             print(f"Data Source Form {index} is new but no file uploaded.")

# #         # Print the changes processed
# #         print("Processing Changes in DataSource:")
# #         print(f"Added Files: {added_files}")
# #         print(f"Updated Files: {updated_files}")
# #         print(f"Deleted Files: {deleted_files}")



# # # Register the DataPipeline model
# # admin.site.register(DataPipeline, DataPipelineAdmin)







from django.contrib import admin
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ..models import DataPipeline, DataSource
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

# # Inline for DataSource, allowing multiple file uploads for a single DataPipeline
# class DataSourceInline(admin.TabularInline):
#     model = DataSource
#     extra = 1  # Show one extra empty file field by default
#     fields = ('file', 'uploaded_at')
#     readonly_fields = ('uploaded_at',)
#     verbose_name_plural = 'Data Sources'

#     def has_add_permission(self, request,obj=None):
#         return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

#     def has_change_permission(self, request, obj=None):
#         if obj is None:
#             return request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser
#         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.update_own_pipeline') or request.user.is_superuser

#     def has_delete_permission(self, request, obj=None):
#         if obj is None:
#             return request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser
#         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.delete_own_pipeline') or request.user.is_superuser

#     def has_view_permission(self, request, obj=None):
#         if obj is None:
#             return request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser
#         return request.user in obj.chatbot.users.all() and request.user.has_perm('data_pipeline.view_own_pipeline') or request.user.is_superuser

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from ..models import DataPipeline, DataSource

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

