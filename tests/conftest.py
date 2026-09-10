"""Configuração global do pytest para o NEXUS V14."""
from __future__ import annotations

import os
import sys

import pytest

# Garante que o pacote raiz (nexus_core, nexus_server, kernel) seja importável
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """
    Executa testes `async def` sem exigir pytest-asyncio.

    O kernel é assíncrono na camada de produção (V11.2); a suíte precisa testar
    isso, mas uma dependência de plugin a mais quebraria a promessa central do
    projeto (rodar com ZERO dependências obrigatórias). Este hook roda o
    coroutine em um event loop novo, com ou sem o plugin instalado.
    """
    import asyncio
    import inspect

    func = pyfuncitem.obj
    if not inspect.iscoroutinefunction(func):
        return None
    kwargs = {nome: pyfuncitem.funcargs[nome]
              for nome in pyfuncitem._fixtureinfo.argnames}
    asyncio.run(func(**kwargs))
    return True


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    """Nenhum teste deve escrever artefatos (db/json) dentro do repositório."""
    monkeypatch.chdir(tmp_path)
    yield
