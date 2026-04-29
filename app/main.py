from datetime import datetime

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.database import (
    create_tables,
    salvar_inspecao_db,
    listar_inspecoes,
    salvar_abertura_turno_db,
    obter_turno_ativo,
    salvar_finalizacao_turno_db,
    obter_hodometro_inicial,
    listar_turnos
)

from app.influx_service import enviar_inspecao, enviar_finalizacao

# Aplicacao principal FastAPI.
app = FastAPI(title="Relatório de Motoristas")

# Disponibiliza arquivos estaticos em /static.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pasta onde ficam os arquivos HTML renderizados pelo Jinja2.
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup():
    # Cria ou atualiza as tabelas locais ao iniciar o servidor.
    create_tables()


@app.get("/")
def login_page(request: Request):
    # Tela inicial com login simples.
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/menu")
def menu_page(request: Request, usuario: str = ""):
    # Menu principal recebe o usuario pela query string.
    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"usuario": usuario}
    )


@app.get("/inspecao")
def inspecao_page(request: Request, usuario: str = ""):
    # A inspecao so pode ser preenchida quando ha um turno aberto.
    turno_ativo = obter_turno_ativo(usuario)

    if not turno_ativo:
        return templates.TemplateResponse(
            request=request,
            name="menu.html",
            context={
                "usuario": usuario,
                "mensagem": "Abra um turno antes de registrar uma inspeção."
            }
        )

    veiculo = turno_ativo[1]
    turno = turno_ativo[2]

    return templates.TemplateResponse(
        request=request,
        name="inspecao.html",
        context={
            "usuario": usuario,
            "veiculo": veiculo,
            "turno": turno
        }
    )


@app.post("/inspecao")
def salvar_inspecao(
    request: Request,
    usuario: str = Form(...),
    veiculo: str = Form(...),
    farois: str = Form(...),
    lanternas: str = Form(...),
    pneus: str = Form(...),
    observacoes: str = Form("")
):
    # Data e hora padronizadas para salvar no SQLite.
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Salva primeiro no banco local.
    salvar_inspecao_db(
        data_hora=data_hora,
        usuario=usuario,
        veiculo=veiculo,
        farois=farois,
        lanternas=lanternas,
        pneus=pneus,
        observacoes=observacoes
    )

    # Envia tambem para o InfluxDB, usado em dashboards externos.
    enviar_inspecao(usuario, veiculo, farois, lanternas, pneus)

    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"usuario": usuario}
    )


@app.get("/historico")
def historico(request: Request):
    # Lista todas as inspecoes cadastradas.
    dados = listar_inspecoes()

    return templates.TemplateResponse(
        request=request,
        name="historico.html",
        context={"dados": dados}
    )


@app.get("/abertura-turno")
def abertura_turno_page(request: Request, usuario: str = ""):
    # Formulario de inicio do turno do motorista.
    return templates.TemplateResponse(
        request=request,
        name="abertura_turno.html",
        context={"usuario": usuario}
    )


@app.post("/abertura-turno")
def salvar_abertura_turno(
    request: Request,
    usuario: str = Form(...),
    veiculo: str = Form(...),
    hodometro_inicial: float = Form(...),
    turno: str = Form(...),
    observacoes: str = Form("")
):
    # Marca o horario de abertura do turno.
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    salvar_abertura_turno_db(
        data_hora=data_hora,
        usuario=usuario,
        veiculo=veiculo,
        hodometro_inicial=hodometro_inicial,
        turno=turno,
        observacoes=observacoes
    )

    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"usuario": usuario}
    )


@app.get("/finalizar-turno")
def finalizar_turno_page(request: Request, usuario: str = ""):
    # Carrega o turno aberto para preencher os dados de encerramento.
    turno_ativo = obter_turno_ativo(usuario)

    if not turno_ativo:
        return templates.TemplateResponse(
            request=request,
            name="menu.html",
            context={
                "usuario": usuario,
                "mensagem": "Não há turno aberto para finalizar."
            }
        )

    abertura_id = turno_ativo[0]
    veiculo = turno_ativo[1]
    turno = turno_ativo[2]
    hodometro_inicial = turno_ativo[3]

    return templates.TemplateResponse(
        request=request,
        name="finalizar_turno.html",
        context={
            "usuario": usuario,
            "abertura_id": abertura_id,
            "veiculo": veiculo,
            "turno": turno,
            "hodometro_inicial": hodometro_inicial
        }
    )


@app.post("/finalizar-turno")
def salvar_finalizacao_turno(
    request: Request,
    abertura_id: int = Form(...),
    usuario: str = Form(...),
    veiculo: str = Form(...),
    turno: str = Form(...),
    hodometro_final: float = Form(...),
    observacoes: str = Form("")
):
    # Registra o horario em que o turno foi finalizado.
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # O hodometro inicial vem da abertura, evitando confiar em valor do formulario.
    hodometro_inicial = obter_hodometro_inicial(abertura_id, usuario)
    if hodometro_inicial is None:
        return templates.TemplateResponse(
            request=request,
            name="menu.html",
            context={
                "usuario": usuario,
                "mensagem": "Não foi possível localizar a abertura deste turno."
            }
        )

    # Calcula a distancia rodada no turno.
    km_rodado = hodometro_final - hodometro_inicial

    # Impede finalizar com hodometro menor do que o inicial.
    if km_rodado < 0:
        return templates.TemplateResponse(
            request=request,
            name="finalizar_turno.html",
            context={
                "usuario": usuario,
                "abertura_id": abertura_id,
                "veiculo": veiculo,
                "turno": turno,
                "hodometro_inicial": hodometro_inicial,
                "mensagem": "O hodômetro final não pode ser menor que o hodômetro inicial."
            }
        )

    # Salva a finalizacao no SQLite.
    salvar_finalizacao_turno_db(
        abertura_id=abertura_id,
        data_hora=data_hora,
        usuario=usuario,
        veiculo=veiculo,
        turno=turno,
        hodometro_final=hodometro_final,
        km_rodado=km_rodado,
        observacoes=observacoes
    )

    # Envia o resumo do turno para o InfluxDB.
    enviar_finalizacao(usuario, veiculo, km_rodado)

    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={
            "usuario": usuario,
            "mensagem": f"Turno finalizado. KM rodado: {km_rodado:.1f}"
        }
    )

@app.get("/historico-turnos")
def historico_turnos(request: Request):
    # Lista os turnos ja encerrados.
    dados = listar_turnos()

    return templates.TemplateResponse(
        request=request,
        name="historico_turnos.html",
        context={"dados": dados}
    )
