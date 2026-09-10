"""Configuração global do pytest para o NEXUS V14."""
from __future__ import annotations

import os
import sys

import pytest

# Garante que o pacote raiz (nexus_core, nexus_server, kernel) seja importável
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    """Nenhum teste deve escrever artefatos (db/json) dentro do repositório."""
    monkeypatch.chdir(tmp_path)
    yield
