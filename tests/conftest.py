import importlib
import sys
import types

import pytest


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    from app import database

    db_path = tmp_path / "relatorio_motoristas_test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    database.create_tables()

    return db_path


@pytest.fixture
def fake_influx(monkeypatch):
    fake_module = types.ModuleType("app.influx_service")
    fake_module.inspecoes = []
    fake_module.finalizacoes = []

    def enviar_inspecao(usuario, veiculo, farois, lanternas, pneus):
        fake_module.inspecoes.append(
            {
                "usuario": usuario,
                "veiculo": veiculo,
                "farois": farois,
                "lanternas": lanternas,
                "pneus": pneus,
            }
        )

    def enviar_finalizacao(usuario, veiculo, km_rodado):
        fake_module.finalizacoes.append(
            {
                "usuario": usuario,
                "veiculo": veiculo,
                "km_rodado": km_rodado,
            }
        )

    fake_module.enviar_inspecao = enviar_inspecao
    fake_module.enviar_finalizacao = enviar_finalizacao

    monkeypatch.setitem(sys.modules, "app.influx_service", fake_module)
    return fake_module


@pytest.fixture
def app_module(monkeypatch, tmp_path, fake_influx):
    from app import database

    db_path = tmp_path / "relatorio_motoristas_app_test.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    sys.modules.pop("app.main", None)
    module = importlib.import_module("app.main")

    return module


@pytest.fixture
def client(app_module):
    from fastapi.testclient import TestClient

    with TestClient(app_module.app) as test_client:
        yield test_client

