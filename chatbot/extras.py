def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Hide the dropdown for non-superusers and show the selected value as plain text."""
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name in ["form", "data_pipeline"]:
            if not request.user.is_superuser:
                # If the user is not a superuser, show the selected value as plain text
                if formfield.queryset.exists():
                    # Check if there's already a selected value and display it as plain text
                    if db_field.name == "form":
                        print(formfield.queryset.first())
                        print(dir(formfield),formfield.bound_data(None,"1"))
                        formfield.label_suffix=": jugnu"
                        formfield.label = formfield.queryset.first().title if formfield.queryset.first() else 'No form selected'
                    elif db_field.name == "data_pipeline":
                        formfield.label = 'sdfsdfsdf:sdfsdf'
                
                # Disable the dropdown for non-superusers
                formfield.widget.attrs['readonly'] = True
                formfield.widget.attrs['style'] = 'display: none;'  # Hide the dropdown

        return formfield

def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Hide the dropdown for non-superusers and show the selected value as plain text."""
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        # Check if this is a change form (meaning there is an object instance)
        obj_id = request.resolver_match.kwargs.get('object_id')
        print(obj_id,"obj_idobj_idobj_idobj_id")
        if obj_id:
            # Get the object instance based on the ID
            obj = self.get_object(request, obj_id)
            print(obj.form,"objobjobjobjobj")
            if obj:
                if db_field.name == "form" and not request.user.is_superuser:
                    # Show the selected form title as plain text
                    if obj.form:
                        formfield.widget.attrs['readonly'] = True
                        formfield.widget.attrs['style'] = 'background-color: #f0f0f0;'  # Make it look read-only
                        formfield.initial = obj.form
                    else:
                        formfield.initial = 'No Form Selected'
                    formfield.disabled = True

                elif db_field.name == "data_pipeline" and not request.user.is_superuser:
                    # Show the selected data pipeline name as plain text
                    if obj.data_pipeline:
                        formfield.widget.attrs['readonly'] = True
                        formfield.widget.attrs['style'] = 'background-color: #f0f0f0;'  # Make it look read-only
                        formfield.initial = obj.data_pipeline
                    else:
                        formfield.initial = 'No Data Pipeline Selected'
                    formfield.disabled = True

        return formfield