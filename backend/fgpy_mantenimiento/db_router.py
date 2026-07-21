class FgpyReadonlyRouter:
    def db_for_write(self, model, **hints):
        if hints.get("database") == "fgpy_readonly":
            return None
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "fgpy_readonly":
            return False
        return None
