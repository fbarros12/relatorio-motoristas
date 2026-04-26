import sqlite3

DB_NAME = "relatorio_motoristas.db"


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS finalizacoes_turno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT NOT NULL,
        usuario TEXT NOT NULL,
        veiculo TEXT NOT NULL,
        turno TEXT NOT NULL,
        hodometro_final REAL NOT NULL,
        observacoes TEXT
    )
    """)

    conn.commit()
    conn.close()


def salvar_abertura_turno_db(data_hora, usuario, veiculo, hodometro_inicial, turno, observacoes):
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspecoes ORDER BY data_hora DESC")
    dados = cursor.fetchall()

    conn.close()
    return dados


def obter_turno_ativo(usuario):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT veiculo, turno
        FROM aberturas_turno
        WHERE usuario = ?
        ORDER BY data_hora DESC
        LIMIT 1
    """, (usuario,))

    resultado = cursor.fetchone()

    conn.close()

    return resultado

def salvar_finalizacao_turno_db(data_hora, usuario, veiculo, turno, hodometro_final, observacoes):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO finalizacoes_turno (
            data_hora,
            usuario,
            veiculo,
            turno,
            hodometro_final,
            observacoes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (data_hora, usuario, veiculo, turno, hodometro_final, observacoes))

    conn.commit()
    conn.close()