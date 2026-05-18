from app import database


def test_salva_e_lista_inspecoes_em_ordem_decrescente(temp_db):
    database.salvar_inspecao_db(
        data_hora="2026-05-18 08:00:00",
        usuario="Ana",
        veiculo="CAM-01",
        farois="OK",
        lanternas="OK",
        pneus="NOK",
        observacoes="Pneu dianteiro",
    )
    database.salvar_inspecao_db(
        data_hora="2026-05-18 09:00:00",
        usuario="Bruno",
        veiculo="CAM-02",
        farois="NOK",
        lanternas="OK",
        pneus="OK",
        observacoes="Farol esquerdo",
    )

    inspecoes = database.listar_inspecoes()

    assert len(inspecoes) == 2
    assert inspecoes[0][1] == "2026-05-18 09:00:00"
    assert inspecoes[0][2] == "Bruno"
    assert inspecoes[1][1] == "2026-05-18 08:00:00"
    assert inspecoes[1][2] == "Ana"


def test_obtem_turno_ativo_mais_recente_e_ignora_turnos_finalizados(temp_db):
    database.salvar_abertura_turno_db(
        data_hora="2026-05-18 07:00:00",
        usuario="Ana",
        veiculo="CAM-01",
        hodometro_inicial=1000.0,
        turno="Manha",
        observacoes="Primeiro turno",
    )
    database.salvar_abertura_turno_db(
        data_hora="2026-05-18 08:00:00",
        usuario="Ana",
        veiculo="CAM-02",
        hodometro_inicial=2000.0,
        turno="Manha",
        observacoes="Segundo turno",
    )

    turno_ativo = database.obter_turno_ativo("Ana")

    assert turno_ativo == (2, "CAM-02", "Manha", 2000.0)

    database.salvar_finalizacao_turno_db(
        abertura_id=2,
        data_hora="2026-05-18 10:00:00",
        usuario="Ana",
        veiculo="CAM-02",
        turno="Manha",
        hodometro_final=2050.0,
        km_rodado=50.0,
        observacoes="Finalizado",
    )

    turno_ativo = database.obter_turno_ativo("Ana")

    assert turno_ativo == (1, "CAM-01", "Manha", 1000.0)


def test_obtem_hodometro_inicial_apenas_do_usuario_dono_da_abertura(temp_db):
    database.salvar_abertura_turno_db(
        data_hora="2026-05-18 07:00:00",
        usuario="Ana",
        veiculo="CAM-01",
        hodometro_inicial=1234.5,
        turno="Manha",
        observacoes="",
    )

    assert database.obter_hodometro_inicial(1, "Ana") == 1234.5
    assert database.obter_hodometro_inicial(1, "Bruno") is None
    assert database.obter_hodometro_inicial(999, "Ana") is None


def test_identifica_abertura_ja_finalizada(temp_db):
    database.salvar_abertura_turno_db(
        data_hora="2026-05-18 07:00:00",
        usuario="Ana",
        veiculo="CAM-01",
        hodometro_inicial=1000.0,
        turno="Manha",
        observacoes="",
    )

    assert database.abertura_ja_finalizada(1) is False

    database.salvar_finalizacao_turno_db(
        abertura_id=1,
        data_hora="2026-05-18 08:00:00",
        usuario="Ana",
        veiculo="CAM-01",
        turno="Manha",
        hodometro_final=1050.0,
        km_rodado=50.0,
        observacoes="",
    )

    assert database.abertura_ja_finalizada(1) is True
    assert database.abertura_ja_finalizada(999) is False


def test_lista_turnos_finalizados_em_ordem_decrescente(temp_db):
    database.salvar_finalizacao_turno_db(
        abertura_id=1,
        data_hora="2026-05-18 08:00:00",
        usuario="Ana",
        veiculo="CAM-01",
        turno="Manha",
        hodometro_final=1050.0,
        km_rodado=50.0,
        observacoes="",
    )
    database.salvar_finalizacao_turno_db(
        abertura_id=2,
        data_hora="2026-05-18 12:00:00",
        usuario="Bruno",
        veiculo="CAM-02",
        turno="Tarde",
        hodometro_final=2200.0,
        km_rodado=80.0,
        observacoes="",
    )

    turnos = database.listar_turnos()

    assert turnos == [
        ("2026-05-18 12:00:00", "Bruno", "CAM-02", "Tarde", 80.0),
        ("2026-05-18 08:00:00", "Ana", "CAM-01", "Manha", 50.0),
    ]
