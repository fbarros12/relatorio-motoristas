import sqlite3

import pytest

from app import database


def _fetch_all(db_path, table):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    conn.close()
    return rows


@pytest.mark.integration
def test_fluxo_completo_do_motorista_persiste_dados_e_renderiza_historicos(
    client,
    fake_influx,
):
    abertura = client.post(
        "/abertura-turno",
        data={
            "usuario": "Carla",
            "veiculo": "TRK-100",
            "hodometro_inicial": "2500.0",
            "turno": "Noite",
            "observacoes": "Inicio sem pendencias",
        },
    )

    assert abertura.status_code == 200
    assert "Menu Principal" in abertura.text

    pagina_inspecao = client.get("/inspecao", params={"usuario": "Carla"})

    assert pagina_inspecao.status_code == 200
    assert "TRK-100" in pagina_inspecao.text

    inspecao = client.post(
        "/inspecao",
        data={
            "usuario": "Carla",
            "veiculo": "TRK-100",
            "farois": "OK",
            "lanternas": "OK",
            "pneus": "NOK",
            "observacoes": "Calibrar pneus ao retornar",
        },
    )

    assert inspecao.status_code == 200
    assert fake_influx.inspecoes == [
        {
            "usuario": "Carla",
            "veiculo": "TRK-100",
            "farois": "OK",
            "lanternas": "OK",
            "pneus": "NOK",
        }
    ]

    historico = client.get("/historico")

    assert historico.status_code == 200
    assert "Histórico de Inspeções" in historico.text
    assert "Carla" in historico.text
    assert "TRK-100" in historico.text
    assert "Calibrar pneus ao retornar" in historico.text

    pagina_finalizar = client.get("/finalizar-turno", params={"usuario": "Carla"})

    assert pagina_finalizar.status_code == 200
    assert 'name="abertura_id" value="1"' in pagina_finalizar.text
    assert "2500.0" in pagina_finalizar.text

    finalizacao = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "1",
            "usuario": "Carla",
            "veiculo": "TRK-100",
            "turno": "Noite",
            "hodometro_final": "2588.4",
            "observacoes": "Turno finalizado normalmente",
        },
    )

    assert finalizacao.status_code == 200
    assert "Turno finalizado. KM rodado: 88.4" in finalizacao.text
    assert fake_influx.finalizacoes == [
        {
            "usuario": "Carla",
            "veiculo": "TRK-100",
            "km_rodado": pytest.approx(88.4),
        }
    ]

    historico_turnos = client.get("/historico-turnos")

    assert historico_turnos.status_code == 200
    assert "Histórico de Turnos" in historico_turnos.text
    assert "Carla" in historico_turnos.text
    assert "TRK-100" in historico_turnos.text
    assert "88.4 km" in historico_turnos.text

    inspecoes = _fetch_all(database.DB_NAME, "inspecoes")
    finalizacoes = _fetch_all(database.DB_NAME, "finalizacoes_turno")

    assert len(inspecoes) == 1
    assert inspecoes[0][2:] == (
        "Carla",
        "TRK-100",
        "OK",
        "OK",
        "NOK",
        "Calibrar pneus ao retornar",
    )
    assert len(finalizacoes) == 1
    assert finalizacoes[0][1] == 1
    assert finalizacoes[0][3:7] == ("Carla", "TRK-100", "Noite", 2588.4)
    assert finalizacoes[0][7] == pytest.approx(88.4)


@pytest.mark.integration
def test_fluxos_de_motoristas_diferentes_mantem_turnos_independentes(client):
    client.post(
        "/abertura-turno",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "hodometro_inicial": "100.0",
            "turno": "Manha",
            "observacoes": "",
        },
    )
    client.post(
        "/abertura-turno",
        data={
            "usuario": "Bruno",
            "veiculo": "CAM-02",
            "hodometro_inicial": "300.0",
            "turno": "Tarde",
            "observacoes": "",
        },
    )

    pagina_ana = client.get("/finalizar-turno", params={"usuario": "Ana"})
    pagina_bruno = client.get("/finalizar-turno", params={"usuario": "Bruno"})

    assert pagina_ana.status_code == 200
    assert 'name="abertura_id" value="1"' in pagina_ana.text
    assert "CAM-01" in pagina_ana.text
    assert "CAM-02" not in pagina_ana.text

    assert pagina_bruno.status_code == 200
    assert 'name="abertura_id" value="2"' in pagina_bruno.text
    assert "CAM-02" in pagina_bruno.text
    assert "CAM-01" not in pagina_bruno.text

    finalizacao_ana = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "1",
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro_final": "125.0",
            "observacoes": "",
        },
    )

    assert finalizacao_ana.status_code == 200
    assert "KM rodado: 25.0" in finalizacao_ana.text

    pagina_bruno_apos_finalizacao_ana = client.get("/finalizar-turno", params={"usuario": "Bruno"})

    assert pagina_bruno_apos_finalizacao_ana.status_code == 200
    assert 'name="abertura_id" value="2"' in pagina_bruno_apos_finalizacao_ana.text
    assert "CAM-02" in pagina_bruno_apos_finalizacao_ana.text

    finalizacoes = _fetch_all(database.DB_NAME, "finalizacoes_turno")

    assert len(finalizacoes) == 1
    assert finalizacoes[0][3:8] == ("Ana", "CAM-01", "Manha", 125.0, 25.0)


@pytest.mark.integration
def test_turno_finalizado_nao_pode_ser_finalizado_novamente(client, fake_influx):
    client.post(
        "/abertura-turno",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "hodometro_inicial": "1000.0",
            "turno": "Manha",
            "observacoes": "",
        },
    )

    primeira_finalizacao = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "1",
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro_final": "1040.0",
            "observacoes": "",
        },
    )

    assert primeira_finalizacao.status_code == 200
    assert "Turno finalizado. KM rodado: 40.0" in primeira_finalizacao.text

    segunda_finalizacao = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "1",
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro_final": "1060.0",
            "observacoes": "Tentativa duplicada",
        },
    )

    assert segunda_finalizacao.status_code == 200
    assert "Este turno já foi finalizado." in segunda_finalizacao.text
    assert fake_influx.finalizacoes == [
        {
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "km_rodado": pytest.approx(40.0),
        }
    ]

    pagina_finalizar = client.get("/finalizar-turno", params={"usuario": "Ana"})

    assert pagina_finalizar.status_code == 200
    assert "Não há turno aberto para finalizar." in pagina_finalizar.text

    finalizacoes = _fetch_all(database.DB_NAME, "finalizacoes_turno")

    assert len(finalizacoes) == 1
    assert finalizacoes[0][7] == pytest.approx(40.0)


@pytest.mark.integration
def test_startup_cria_tabelas_em_banco_limpo(client):
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name IN ('inspecoes', 'aberturas_turno', 'finalizacoes_turno')
        ORDER BY name
        """
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert tables == ["aberturas_turno", "finalizacoes_turno", "inspecoes"]
