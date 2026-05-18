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

