from django.contrib import admin
from .models import DataPipeline, DataSource
from chatbot.models import Chatbot
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

class DataSourceAdminForm(forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ['file', 'data_pipeline']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'accept': settings.ALLOWED_FILE_TYPES})

class DataSourceInline(admin.TabularInline):
    model = DataSource
    extra = 1
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    verbose_name_plural = 'Data Sources'
    form = DataSourceAdminForm

class DataPipelineAdminForm(forms.ModelForm):
    class Meta:
        model = DataPipeline
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('status') == 'pending':
            raise ValidationError(f"The pipeline '{cleaned_data.get('name')}' is on training and cannot be updated.")
        return cleaned_data

class DataPipelineAdmin(admin.ModelAdmin):
    inlines = [DataSourceInline]
    list_display = ('name', 'chatbot', 'url', 'created_at', "status")
    readonly_fields = ('created_at', "updated_at")
    search_fields = ('name', 'url')

    fieldsets = (
        (None, {
            'fields': ('name', 'chatbot', 'url', 'created_at', "status", "updated_at"),
        }),
    )

    # def save_related(self, request, form, formsets, change):
    #     """
    #     Override save_related to capture added, updated, and deleted DataSource instances.
    #     """
    #     super().save_related(request, form, formsets, change)

    #     # Initialize lists to track changes
    #     added_files = []
    #     updated_files = []
    #     deleted_files = []

    #     # Iterate through the formsets
    #     for formset in formsets:
    #         print("Formset received:", formset)  # Debug print
    #         print(f"Formset type: {type(formset)}")  # Print the type of formset for verification
            
    #         # Check if the formset class name is DataSourceFormFormSet
    #         if formset.__class__.__name__ == 'DataSourceFormFormSet':
    #             print("Processing DataSourceInline formset")
    #             for index, data_source_form in enumerate(formset.forms):
    #                 print(f"Data Source Form {index} Instance: {data_source_form.instance}")
    #                 print("Cleaned Data:", data_source_form.cleaned_data)  # Show cleaned data for debugging
                    
    #                 # Check for deletions
    #                 if data_source_form.cleaned_data.get('DELETE', False):
    #                     deleted_files.append(data_source_form.instance.file.name if data_source_form.instance.file else "No file")
    #                     print(f"Data Source Form {index} marked for deletion.")

    #                 elif data_source_form.instance.pk:  # Existing DataSource
    #                     if data_source_form.has_changed():  # Check if it was updated
    #                         updated_files.append(data_source_form.instance.file.name)
    #                         print(f"Data Source Form {index} updated to: {data_source_form.instance.file.name}")

    #                 else:  # New DataSource
    #                     if data_source_form.cleaned_data.get('file'):
    #                         added_files.append(data_source_form.cleaned_data['file'].name)
    #                         print(f"New DataSource added: {data_source_form.cleaned_data['file'].name}")
    #                     else:
    #                         print(f"Data Source Form {index} is new but no file uploaded.")

    #     # Print the changes processed
    #     print("Processing Changes in DataSource:")
    #     print(f"Added Files: {added_files}")
    #     print(f"Updated Files: {updated_files}")
    #     print(f"Deleted Files: {deleted_files}")

        # Other methods remain unchanged...

    def save_related(self, request, form, formsets, change):
        """
        Override save_related to capture added, updated, and deleted DataSource instances.
        """
        super().save_related(request, form, formsets, change)

        # Initialize lists to track changes
        added_files = []
        updated_files = []
        deleted_files = []
        print(change,"change")
        # Iterate through the formsets
        for formset in formsets:
            print("Formset received:", formset)  # Debug print
            print(f"Formset type: {type(formset)}")  # Print the type of formset for verification
            
            # Check if the formset class name is DataSourceFormFormSet
            if formset.__class__.__name__ == 'DataSourceFormFormSet':
                print("Processing DataSourceInline formset")
                for index, data_source_form in enumerate(formset.forms):
                    print(f"Data Source Form {index} Instance: {data_source_form.instance}")
                    print(str(data_source_form.instance.file))
                    print("Cleaned Data:", data_source_form.cleaned_data)  # Show cleaned data for debugging

                    # Get the current file in the database
                    current_file = data_source_form.instance.file.name if data_source_form.instance.file else None
                    print(data_source_form.instance.pk,"data_source_form.instance.pk")
                    # Check for deletions
                    if data_source_form.cleaned_data.get('DELETE', False):
                        deleted_files.append(current_file if current_file else "No file")
                        print(f"Data Source Form {index} marked for deletion.")

                    elif data_source_form.instance.pk:  # Existing DataSource
                        new_file = data_source_form.cleaned_data.get('file')  # The new file uploaded
                        if new_file:  # If a new file is uploaded
                            # Mark the old file as deleted if it's being replaced
                            updated_files.append(new_file.name)  # Log the new file as updated
                            print(f"Data Source Form {index} updated from {current_file} to: {new_file.name}")

                        else:
                            print(f"Data Source Form {index} has no new file uploaded; current file remains: {current_file}")

                    else:  # New DataSource
                        if data_source_form.cleaned_data.get('file'):
                            added_files.append(data_source_form.cleaned_data['file'].name)
                            print(f"New DataSource added: {data_source_form.cleaned_data['file'].name}")
                        else:
                            print(f"Data Source Form {index} is new but no file uploaded.")

        # Print the changes processed
        print("Processing Changes in DataSource:")
        print(f"Added Files: {added_files}")
        print(f"Updated Files: {updated_files}")
        print(f"Deleted Files: {deleted_files}")



# Register the DataPipeline model
admin.site.register(DataPipeline, DataPipelineAdmin)