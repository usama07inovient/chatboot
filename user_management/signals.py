from django.db.models.signals import m2m_changed
from django.contrib.auth.models import Group, Permission
from django.dispatch import receiver
from user_management.models import User  # Replace with your actual User model

# Signal 1: Handle changes in user group memberships (already implemented)
@receiver(m2m_changed, sender=User.groups.through)
def update_user_permissions_on_group_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add' or action == 'post_remove':
        # Get all permissions directly associated with the user's current groups
        current_group_permissions = Permission.objects.filter(group__user=instance).distinct()

        # Get the user's custom permissions (those directly assigned to the user)
        custom_permissions = instance.user_permissions.all()

        # Remove all current group-based permissions
        instance.user_permissions.clear()

        # Reapply custom permissions so they remain intact
        instance.user_permissions.set(custom_permissions)

        # Reassign group permissions
        for perm in current_group_permissions:
            if not instance.user_permissions.filter(pk=perm.pk).exists():
                instance.user_permissions.add(perm)

        # Save the updated permissions for the user
        instance.save()

# Signal 2: Handle changes in group permissions
@receiver(m2m_changed, sender=Group.permissions.through)
def update_users_on_group_permission_change(sender, instance, action, pk_set, **kwargs):
    """
    Handles changes in permissions for a group. When permissions are added or removed from a group, 
    this updates all users in the group.
    
    :param instance: The group instance.
    :param action: The action that triggered the signal ('post_add', 'post_remove').
    :param pk_set: The set of permission primary keys being added/removed.
    """
    if action == 'post_add' or action == 'post_remove':
        # Get all users that belong to this group
        users_in_group = User.objects.filter(groups=instance)

        for user in users_in_group:
            # Get the user's current permissions
            user_permissions = user.user_permissions.all()

            if action == 'post_add':
                # When permissions are added to the group, add them to the user if they don't already have them
                for perm_id in pk_set:
                    permission = Permission.objects.get(pk=perm_id)
                    if permission not in user_permissions:
                        user.user_permissions.add(permission)

            elif action == 'post_remove':
                # When permissions are removed from the group, remove them from the user 
                # only if it's a group-based permission (and not a custom one)
                for perm_id in pk_set:
                    permission = Permission.objects.get(pk=perm_id)
                    # Remove the permission only if the user does not have it as a custom permission
                    if permission in user_permissions and not user.has_perm(permission.codename):
                        user.user_permissions.remove(permission)

            # Save the user's updated permissions
            user.save()
