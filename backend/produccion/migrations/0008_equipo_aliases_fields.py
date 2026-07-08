# feature/equipo-aliases (2026-07-08)
# Migracion limpia: solo agrega los 4 campos del feature.
# Los cambios pre-existentes no-migrados (Origen, AlterModelOptions,
# 9 AddField a RegistroProduccion, AlterField unidad_negocio con
# db_column inconsistente) quedan para otro PR.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0007_add_unidadnegocio_to_equipo'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            SET @old_sql_mode_equipo_aliases = @@SESSION.sql_mode;
            SET SESSION sql_mode = REPLACE(REPLACE(@@SESSION.sql_mode, 'NO_ZERO_IN_DATE', ''), 'NO_ZERO_DATE', '');
            SET SESSION sql_mode = REPLACE(REPLACE(@@SESSION.sql_mode, ',,', ','), ',,', ',');
            SET SESSION sql_mode = TRIM(BOTH ',' FROM @@SESSION.sql_mode);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE `moviles` ADD COLUMN `aliases` json DEFAULT ('[]') NOT NULL;
                    ALTER TABLE `moviles` ADD COLUMN `codigo_fg` varchar(30) DEFAULT '' NOT NULL;
                    ALTER TABLE `moviles` ALTER COLUMN `codigo_fg` DROP DEFAULT;
                    ALTER TABLE `moviles` ADD COLUMN `modelo_normalizado` varchar(80) DEFAULT '' NOT NULL;
                    ALTER TABLE `moviles` ALTER COLUMN `modelo_normalizado` DROP DEFAULT;
                    ALTER TABLE `moviles` ADD COLUMN `ultima_sync_filtros` datetime(6) NULL;
                    CREATE INDEX `moviles_codigo_fg_02701137` ON `moviles` (`codigo_fg`);
                    """,
                    reverse_sql="""
                    DROP INDEX `moviles_codigo_fg_02701137` ON `moviles`;
                    ALTER TABLE `moviles`
                        DROP COLUMN `ultima_sync_filtros`,
                        DROP COLUMN `modelo_normalizado`,
                        DROP COLUMN `codigo_fg`,
                        DROP COLUMN `aliases`;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='equipo',
                    name='aliases',
                    field=models.JSONField(blank=True, default=list),
                ),
                migrations.AddField(
                    model_name='equipo',
                    name='codigo_fg',
                    field=models.CharField(blank=True, db_index=True, default='', max_length=30),
                ),
                migrations.AddField(
                    model_name='equipo',
                    name='modelo_normalizado',
                    field=models.CharField(blank=True, default='', max_length=80),
                ),
                migrations.AddField(
                    model_name='equipo',
                    name='ultima_sync_filtros',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
        migrations.RunSQL(
            sql="SET SESSION sql_mode = @old_sql_mode_equipo_aliases;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
