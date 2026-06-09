import sqlite3

from app import database


def test_login_e_menu_renderizam(client):
    login = client.get("/")
    menu = client.get("/menu", params={"usuario": "Ana"})

    assert login.status_code == 200
    assert "Login" in login.text
    assert menu.status_code == 200
    assert "Menu Principal" in menu.text
    assert "Ana" in menu.text


def test_inspecao_exige_turno_aberto(client):
    response = client.get("/inspecao", params={"usuario": "Ana"})

    assert response.status_code == 200
    assert "Abra um turno antes de registrar uma inspeção." in response.text


def test_abastecimento_exige_turno_aberto(client):
    response = client.get("/abastecimento", params={"usuario": "Ana"})

    assert response.status_code == 200
    assert "Abra um turno antes de registrar um abastecimento." in response.text


def test_downtime_exige_turno_aberto(client):
    response = client.get("/downtime", params={"usuario": "Ana"})

    assert response.status_code == 200
    assert "Abra um turno antes de registrar um downtime." in response.text


def test_fluxo_de_downtime_abre_com_dados_do_turno_ativo(client):
    menu = client.get("/menu", params={"usuario": "Ana"})

    assert "/downtime?usuario=Ana" in menu.text

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

    pagina_downtime = client.get("/downtime", params={"usuario": "Ana"})

    assert pagina_downtime.status_code == 200
    assert "Registro de Downtime" in pagina_downtime.text
    assert 'name="veiculo" value="CAM-01"' in pagina_downtime.text
    assert 'name="turno" value="Manha"' in pagina_downtime.text


def test_fluxo_de_downtime_salva_tempo_parado_calculado(client):
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

    response = client.post(
        "/downtime",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "categoria": "Manutenção",
            "hora_inicio": "2026-05-18T08:15",
            "hora_fim": "2026-05-18T09:45",
            "observacoes": "Troca de correia",
        },
    )

    assert response.status_code == 200
    assert "Downtime salvo com sucesso. Tempo parado: 90.0 min." in response.text

    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT usuario, veiculo, turno, categoria, hora_inicio, hora_fim, tempo_parado_min, observacoes
        FROM downtimes
    """)
    downtimes = cursor.fetchall()
    conn.close()

    assert downtimes == [
        (
            "Ana",
            "CAM-01",
            "Manha",
            "Manutenção",
            "2026-05-18T08:15",
            "2026-05-18T09:45",
            90.0,
            "Troca de correia",
        )
    ]


def test_downtime_rejeita_hora_final_menor_que_inicial(client):
    response = client.post(
        "/downtime",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "categoria": "Clima",
            "hora_inicio": "2026-05-18T10:00",
            "hora_fim": "2026-05-18T09:00",
            "observacoes": "",
        },
    )

    assert response.status_code == 200
    assert "A hora final não pode ser menor que a hora inicial." in response.text

    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM downtimes")
    total = cursor.fetchone()[0]
    conn.close()

    assert total == 0


def test_fluxo_de_abastecimento_salva_dados_do_turno_ativo(client):
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

    pagina_abastecimento = client.get("/abastecimento", params={"usuario": "Ana"})

    assert pagina_abastecimento.status_code == 200
    assert "Abastecimento" in pagina_abastecimento.text
    assert 'name="veiculo" value="CAM-01"' in pagina_abastecimento.text
    assert 'name="turno" value="Manha"' in pagina_abastecimento.text

    response = client.post(
        "/abastecimento",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro": "1010.5",
            "litros": "35.25",
            "combustivel": "Diesel S10",
            "observacoes": "Posto central",
        },
    )

    assert response.status_code == 200
    assert "Abastecimento salvo com sucesso." in response.text

    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT usuario, veiculo, turno, hodometro, litros, combustivel, observacoes
        FROM abastecimentos
    """)
    abastecimentos = cursor.fetchall()
    conn.close()

    assert abastecimentos == [
        ("Ana", "CAM-01", "Manha", 1010.5, 35.25, "Diesel S10", "Posto central")
    ]

    historico = client.get("/historico-abastecimentos", params={"usuario": "Ana"})

    assert historico.status_code == 200
    assert "Histórico de Abastecimentos" in historico.text
    assert "CAM-01" in historico.text
    assert "Diesel S10" in historico.text
    assert "35.25 L" in historico.text
    assert "Posto central" in historico.text


def test_fluxo_de_abertura_inspecao_e_finalizacao(client, fake_influx):
    abertura = client.post(
        "/abertura-turno",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "hodometro_inicial": "1000.0",
            "turno": "Manha",
            "observacoes": "Inicio normal",
        },
    )

    assert abertura.status_code == 200
    assert "Menu Principal" in abertura.text

    pagina_inspecao = client.get("/inspecao", params={"usuario": "Ana"})

    assert pagina_inspecao.status_code == 200
    assert "CAM-01" in pagina_inspecao.text
    assert "Inspeção" in pagina_inspecao.text

    inspecao = client.post(
        "/inspecao",
        data={
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "farois": "OK",
            "lanternas": "NOK",
            "pneus": "OK",
            "observacoes": "Lanterna direita",
        },
    )

    assert inspecao.status_code == 200
    assert fake_influx.inspecoes == [
        {
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "farois": "OK",
            "lanternas": "NOK",
            "pneus": "OK",
        }
    ]

    historico = client.get("/historico")

    assert historico.status_code == 200
    assert "Lanterna direita" in historico.text

    pagina_finalizar = client.get("/finalizar-turno", params={"usuario": "Ana"})

    assert pagina_finalizar.status_code == 200
    assert 'name="abertura_id" value="1"' in pagina_finalizar.text
    assert "1000.0" in pagina_finalizar.text

    finalizacao = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "1",
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro_final": "1042.5",
            "observacoes": "Sem ocorrencias",
        },
    )

    assert finalizacao.status_code == 200
    assert "Turno finalizado. KM rodado: 42.5" in finalizacao.text
    assert fake_influx.finalizacoes == [
        {
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "km_rodado": 42.5,
        }
    ]

    historico_turnos = client.get("/historico-turnos")

    assert historico_turnos.status_code == 200
    assert "42.5" in historico_turnos.text


def test_finalizacao_rejeita_hodometro_menor_que_inicial(client, fake_influx):
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

    response = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "1",
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro_final": "999.9",
            "observacoes": "",
        },
    )

    assert response.status_code == 200
    assert "O hodômetro final não pode ser menor que o hodômetro inicial." in response.text
    assert fake_influx.finalizacoes == []


def test_finalizacao_rejeita_abertura_inexistente(client, fake_influx):
    response = client.post(
        "/finalizar-turno",
        data={
            "abertura_id": "999",
            "usuario": "Ana",
            "veiculo": "CAM-01",
            "turno": "Manha",
            "hodometro_final": "1000.0",
            "observacoes": "",
        },
    )

    assert response.status_code == 200
    assert "Não foi possível localizar a abertura deste turno." in response.text
    assert fake_influx.finalizacoes == []
