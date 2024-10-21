from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django import forms
from django.utils.html import format_html
from .models import User
from chatbot.models import Chatbot
from data_pipeline.models import DataPipeline  # Import other apps with custom permissions
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Permission
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group, Permission
from django import forms
from django.utils.html import format_html
from django.contrib.admin.widgets import FilteredSelectMultiple

# Define the custom permissions for each app
CUSTOM_PERMISSIONS = {
    'chatbot': [
        'create_own_chatbot', 'delete_own_chatbot', 'update_own_chatbot', 'view_own_chatbot',
        'activate_chatbot', 'modify_chat_save_session'
    ],
    'form': [
        'add_own_form', 'update_own_form', 'delete_own_form', 'view_own_form'
    ],
    'data_pipeline': [
        'add_own_pipeline', 'update_own_pipeline', 'delete_own_pipeline', 'view_own_pipeline'
    ]
}

# Custom form for adding a new User
class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'platform_name', 'profile_pic', 'logo', 'website_url', 'date_of_subscription')

# Custom form to manage custom app permissions using FilteredSelectMultiple
class CustomUserChangeForm(forms.ModelForm):
    custom_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(
            codename__in=[perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]  # Fetch only defined custom permissions
        ),
        widget=FilteredSelectMultiple("Custom App Permissions", is_stacked=False),
        required=False,
        label="Custom App Permissions"
    )

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Fetch the initial custom permissions for this user, both from the user and the user's groups
            initial_permissions = self._get_initial_permissions()

            # Set the initial selected custom permissions
            self.fields['custom_permissions'].initial = initial_permissions

    def _get_initial_permissions(self):
        """
        Helper method to get permissions from the user's groups as well as the user itself.
        """
        # Get permissions directly assigned to the user
        user_permissions = self.instance.user_permissions.filter(
            codename__in=[perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]
        )

        # Get permissions assigned through groups
        group_permissions = Permission.objects.filter(
            group__user=self.instance,
            codename__in=[perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]
        ).distinct()

        # Combine user and group permissions
        initial_permissions = list(user_permissions) + list(group_permissions)
        return initial_permissions

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

        if user.pk:
            # Get the list of custom permissions
            custom_permission_codenames = [perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]

            # Remove existing custom permissions
            existing_permissions = user.user_permissions.filter(codename__in=custom_permission_codenames)
            for perm in existing_permissions:
                user.user_permissions.remove(perm)

            # Add selected custom permissions
            selected_permissions = self.cleaned_data['custom_permissions']
            for perm in selected_permissions:
                user.user_permissions.add(perm)

        return user

class ChatbotInline(admin.TabularInline):
    model = Chatbot.users.through  # Access the intermediary model for the Many-to-Many relationship
    extra = 1  # How many empty rows to show for adding new relationships
    verbose_name = 'Assigned Chatbot'
    verbose_name_plural = 'Assigned Chatbots'
    fields = ('chatbot', 'platform_key', 'created_at', 'is_active', 'actions')  # Use the actual field 'chatbot'
    readonly_fields = ('platform_key', 'created_at', 'is_active', 'actions')  # Fields to be displayed as read-only

    def get_queryset(self, request):
        """Limit the displayed chatbots to those available for assignment."""
        queryset = super().get_queryset(request)
        return queryset.select_related('chatbot')

    # Method to display the platform key of the selected chatbot
    def platform_key(self, obj):
        return obj.chatbot.platform_key if obj.pk else '-'

    platform_key.short_description = "Platform Key"

    # Method to display the creation date of the selected chatbot
    def created_at(self, obj):
        return obj.chatbot.created_at if obj.pk else '-'

    created_at.short_description = "Created At"

    # Method to display whether the chatbot is active or not
    def is_active(self, obj):
        return 'Active' if obj.chatbot.is_active else 'Inactive'

    is_active.short_description = "Is Active"

    # Method to display the action buttons (Edit/Remove) for the selected chatbot
    def actions(self, obj):
        if obj.pk:
            edit_url = reverse('admin:chatbot_chatbot_change', args=[obj.chatbot.pk])
            remove_url = reverse('chatbot_chatbot_remove_relation', args=[obj.chatbot.pk, obj.user.pk])
            return format_html(
                '''
                <a class="button" href="{}">Edit</a>
                ''',
                edit_url, remove_url
            )

        return '-'

    actions.short_description = "Actions"

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of chatbots assigned to users."""
        return True

# Extend the UserAdmin to include the custom fields from the User model
class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = CustomUserChangeForm

    # Main fieldsets
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'platform_name', 'profile_pic', 'logo', 'website_url', 'date_of_subscription', 'password')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'platform_name', 'profile_pic', 'logo', 'website_url', 'date_of_subscription', 'password1', 'password2')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    inlines = [ChatbotInline]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        add_chatbot_url = reverse('admin:chatbot_chatbot_add') + f'?user={object_id}'
        extra_context['add_chatbot_button'] = format_html('<a class="button" href="{}">Add another Chatbot</a>', add_chatbot_url)
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    list_display = ('username', 'email', 'platform_name', 'date_of_subscription', 'last_login', 'date_joined')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    change_form_template = 'admin/user_change_form.html'

    # def save_model(self, request, obj, form, change):
    #     # Retrieve user's custom permissions before saving
    #     custom_permissions = set(obj.user_permissions.all())

    #     super().save_model(request, obj, form, change)

    #     # Restore the user's custom permissions after saving the user
    #     obj.user_permissions.set(custom_permissions)

    def save_model(self, request, obj, form, change):
        # Save the user object first so that it has a valid primary key (id)
        super().save_model(request, obj, form, change)

        # Handle the Many-to-Many relationship for chatbots after the user has been saved
        if form.cleaned_data.get('chatbots'):
            obj.chatbots.set(form.cleaned_data['chatbots'])  # Set the related chatbots


        # Optionally, handle group changes here as well
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Example: You could add logic here to inform the admin about custom vs group permissions
        return form

# Custom form to manage custom app permissions using FilteredSelectMultiple for Group
class CustomGroupChangeForm(forms.ModelForm):
    custom_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(
            codename__in=[perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]
        ),
        widget=FilteredSelectMultiple("Custom App Permissions", is_stacked=False),
        required=False,
        label="Custom App Permissions"
    )

    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Fetch the initial custom permissions for this group
            initial_permissions = self.instance.permissions.filter(
                codename__in=[perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]
            )
            self.fields['custom_permissions'].initial = initial_permissions

    def save(self, commit=True):
        group = super().save(commit=False)

        if commit:
            group.save()

        if group.pk:
            # Get the list of custom permissions
            custom_permission_codenames = [perm for perms in CUSTOM_PERMISSIONS.values() for perm in perms]

            # Remove existing custom permissions
            existing_permissions = group.permissions.filter(codename__in=custom_permission_codenames)
            for perm in existing_permissions:
                group.permissions.remove(perm)

            # Add selected custom permissions
            selected_permissions = self.cleaned_data.get('custom_permissions', [])
            for perm in selected_permissions:
                group.permissions.add(perm)

        return group

# Extend the GroupAdmin to include only custom permissions
class CustomGroupAdmin(GroupAdmin):
    form = CustomGroupChangeForm

    # Override the fieldsets to exclude 'custom_permissions'
    fieldsets = (
        (None, {'fields': ('name',)}),  # No 'custom_permissions' field here
    )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Inject custom context for the change view.
        """
        extra_context = extra_context or {}
        group = self.get_object(request, object_id)
        # Add custom app permissions to context to display it manually
        form = self.get_form(request, obj=group)
        extra_context['custom_permissions'] = form.base_fields['custom_permissions']
        return super().change_view(request, object_id, form_url, extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Add custom permissions to the admin form.
        """
        form = self.get_form(request, obj=obj)
        context['adminform'].form.custom_permissions = form.base_fields.get('custom_permissions')
        return super().render_change_form(request, context, add, change, form_url, obj)

# Register the custom GroupAdmin
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

# Register the UserAdmin
admin.site.register(User, CustomUserAdmin)