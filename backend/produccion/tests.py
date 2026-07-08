import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from produccion.management.commands.sync_filtros import (
    inferir_modelo_normalizado,
    load_fg_env,
)


class SyncFiltrosHelpersTests(SimpleTestCase):
    def test_inferir_modelo_descarta_prefijos_operativos(self):
        casos = {
            'Forwarder PONSSE BUFFALO KING - Nº 1': 'Ponsse Buffalo King',
            'Feller JOHN DEERE 959M - Nº 1': 'John Deere 959M',
            'Camión VOLVO FH540 - AC910XT': 'Volvo FH540',
        }

        for detalle, esperado in casos.items():
            with self.subTest(detalle=detalle):
                self.assertEqual(inferir_modelo_normalizado(detalle), esperado)

    def test_load_fg_env_prioriza_env_vars_sobre_fg_env_path_y_cwd_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cwd_env = tmp / '.env'
            pointed_env = tmp / 'fg.env'
            cwd_env.write_text(
                'FG_API_URL=http://cwd.example\n'
                'FG_USER=cwd-user\n'
                'FG_PASSWORD=cwd-pass\n',
                encoding='utf-8',
            )
            pointed_env.write_text(
                'FG_API_URL=http://file.example\n'
                'FG_USER=file-user\n'
                'FG_PASSWORD=file-pass\n',
                encoding='utf-8',
            )

            old_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with patch.dict(os.environ, {
                    'FG_ENV_PATH': str(pointed_env),
                    'FG_API_URL': 'http://env.example',
                    'FG_USER': 'env-user',
                    'FG_PASSWORD': 'env-pass',
                }, clear=True):
                    env = load_fg_env()
            finally:
                os.chdir(old_cwd)

        self.assertEqual(env['FG_API_URL'], 'http://env.example')
        self.assertEqual(env['FG_USER'], 'env-user')
        self.assertEqual(env['FG_PASSWORD'], 'env-pass')

    def test_load_fg_env_usa_fg_env_path_si_no_hay_env_vars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pointed_env = Path(tmpdir) / 'fg.env'
            pointed_env.write_text(
                'FG_API_URL=http://file.example\n'
                'FG_USER=file-user\n'
                'FG_PASSWORD=file-pass\n',
                encoding='utf-8',
            )

            with patch.dict(os.environ, {'FG_ENV_PATH': str(pointed_env)}, clear=True):
                env = load_fg_env()

        self.assertEqual(env['FG_API_URL'], 'http://file.example')
        self.assertEqual(env['FG_USER'], 'file-user')
        self.assertEqual(env['FG_PASSWORD'], 'file-pass')
