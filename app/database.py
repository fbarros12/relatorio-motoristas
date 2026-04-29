import sqlite3

# Nome do arquivo SQLite usado pela aplicacao local.
DB_NAME = "relatorio_motoristas.db"


def create_tables():
    # Garante que todas as tabelas existam antes da aplicacao receber uso.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Historico das inspecoes feitas durante o turno do motorista.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspecoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            usuario TEXT NOT NULL,
            veiculo TEXT NOT NULL,
            farois TEXT NOT NULL,
            lanternas TEXT NOT NULL,
            pneus TEXT NOT NULL,
            observacoes TEXT
        )
    """)

    # Registro de inicio de turno, incluindo veiculo e hodometro inicial.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aberturas_turno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            usuario TEXT NOT NULL,
            veiculo TEXT NOT NULL,
            hodometro_inicial REAL NOT NULL,
            turno TEXT NOT NULL,
            observacoes TEXT
        )
    """)

    # Registro de encerramento do turno, com calculo de quilometragem.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finalizacoes_turno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abertura_id INTEGER,
            data_hora TEXT NOT NULL,
            usuario TEXT NOT NULL,
            veiculo TEXT NOT NULL,
            turno TEXT NOT NULL,
            hodometro_final REAL NOT NULL,
            km_rodado REAL NOT NULL,
            observacoes TEXT
        )
    """)

    # Mantem compatibilidade com bancos criados antes desses campos existirem.
    cursor.execute("PRAGMA table_info(finalizacoes_turno)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]
    if "abertura_id" not in colunas:
        cursor.execute("ALTER TABLE finalizacoes_turno ADD COLUMN abertura_id INTEGER")
    if "km_rodado" not in colunas:
        cursor.execute("ALTER TABLE finalizacoes_turno ADD COLUMN km_rodado REAL DEFAULT 0")

    conn.commit()
    conn.close()


def salvar_abertura_turno_db(data_hora, usuario, veiculo, hodometro_inicial, turno, observacoes):
    # Insere uma nova abertura de turno no banco local.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO aberturas_turno (
            data_hora,
            usuario,
            veiculo,
            hodometro_inicial,
            turno,
            observacoes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (data_hora, usuario, veiculo, hodometro_inicial, turno, observacoes))

    conn.commit()
    conn.close()


def salvar_inspecao_db(data_hora, usuario, veiculo, farois, lanternas, pneus, observacoes):
    # Persiste a inspecao preenchida pelo motorista.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inspecoes (
            data_hora,
            usuario,
            veiculo,
            farois,
            lanternas,
            pneus,
            observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data_hora, usuario, veiculo, farois, lanternas, pneus, observacoes))

    conn.commit()
    conn.close()


def listar_inspecoes():
    # Retorna as inspecoes mais recentes primeiro para a tela de historico.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspecoes ORDER BY data_hora DESC")
    dados = cursor.fetchall()

    conn.close()
    return dados


def obter_turno_ativo(usuario):
    # Busca a abertura mais recente do usuario que ainda nao tem finalizacao.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.veiculo, a.turno, a.hodometro_inicial
        FROM aberturas_turno a
        WHERE a.usuario = ?
          AND NOT EXISTS (
              SELECT 1
              FROM finalizacoes_turno f
              WHERE f.abertura_id = a.id
                 OR (
                    f.abertura_id IS NULL
                    AND f.usuario = a.usuario
                    AND f.veiculo = a.veiculo
                    AND f.turno = a.turno
                    AND f.data_hora >= a.data_hora
                 )
          )
        ORDER BY a.data_hora DESC
        LIMIT 1
    """, (usuario,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado


def obter_hodometro_inicial(abertura_id, usuario):
    # Confere o hodometro inicial do turno antes de calcular o km rodado.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hodometro_inicial
        FROM aberturas_turno
        WHERE id = ? AND usuario = ?
        LIMIT 1
    """, (abertura_id, usuario))

    resultado = cursor.fetchone()
    conn.close()

    if not resultado:
        return None

    return resultado[0]


def salvar_finalizacao_turno_db(abertura_id, data_hora, usuario, veiculo, turno, hodometro_final, km_rodado, observacoes):
    # Salva o encerramento do turno com a quilometragem ja calculada.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO finalizacoes_turno (
            abertura_id,
            data_hora,
            usuario,
            veiculo,
            turno,
            hodometro_final,
            km_rodado,
            observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (abertura_id, data_hora, usuario, veiculo, turno, hodometro_final, km_rodado, observacoes))

    conn.commit()
    conn.close()


def listar_turnos():
    # Retorna os turnos finalizados para o historico.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT data_hora, usuario, veiculo, turno, km_rodado
        FROM finalizacoes_turno
        ORDER BY data_hora DESC
    """)

    dados = cursor.fetchall()
    conn.close()

    return dados
