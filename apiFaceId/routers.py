
class ReportesRouter:
    """
    Un router para controlar las operaciones de base de datos de la tabla Reportes.
    """

    def db_for_read(self, model, **hints):
        """Envia lecturas del modelo Reportes a la base de datos 'neon'."""
        if model._meta.app_label == 'reportes':
            return 'neon'
        return None

    def db_for_write(self, model, **hints):
        """Envia escrituras del modelo Reportes a la base de datos 'neon'."""
        if model._meta.app_label == 'reportes':
            return 'neon'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Permite relaciones si ambos objetos están en la misma base de datos."""
        db_set = {'default', 'neon'}
        if {obj1._state.db, obj2._state.db}.issubset(db_set):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Permite migraciones solo en las bases de datos correspondientes."""
        if app_label == 'reportes':
            return db == 'neon'
        return db == 'default'
