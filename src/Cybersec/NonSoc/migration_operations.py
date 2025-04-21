from django.db.migrations.operations.base import Operation

class SafeRemoveField(Operation):
    """
    A migration operation that safely removes a field, checking if it exists first.
    This is particularly useful for SQLite which doesn't fully support ALTER TABLE DROP COLUMN.
    """
    
    reduces_to_sql = True
    reversible = True
    
    def __init__(self, model_name, name):
        self.model_name = model_name
        self.name = name
    
    def state_forwards(self, app_label, state):
        # Remove the field from the model state
        model_state = state.models[app_label, self.model_name.lower()]
        for field_name in list(model_state.fields):
            if field_name == self.name:
                del model_state.fields[field_name]
    
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # Check if the column exists first
        model = from_state.apps.get_model(app_label, self.model_name)
        if self.name in [f.name for f in model._meta.local_fields]:
            schema_editor.remove_field(model, model._meta.get_field(self.name))
    
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # Add the field back
        model = to_state.apps.get_model(app_label, self.model_name)
        if self.name in [f.name for f in model._meta.local_fields]:
            schema_editor.add_field(model, model._meta.get_field(self.name))
    
    def describe(self):
        return f"Safely remove field {self.name} from {self.model_name}"
