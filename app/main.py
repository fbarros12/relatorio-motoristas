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
    salvar_finalizacao_turno_db
)

app = FastAPI(title="Relatório de Motoristas")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/menu")
def menu_page(request: Request, usuario: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"usuario": usuario}
    )


@app.get("/inspecao")
def inspecao_page(request: Request, usuario: str = ""):
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

    veiculo = turno_ativo[0]
    turno = turno_ativo[1]

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
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    salvar_inspecao_db(
        data_hora=data_hora,
        usuario=usuario,
        veiculo=veiculo,
        farois=farois,
        lanternas=lanternas,
        pneus=pneus,
        observacoes=observacoes
    )

    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"usuario": usuario}
    )


@app.get("/historico")
def historico(request: Request):
    dados = listar_inspecoes()

    return templates.TemplateResponse(
        request=request,
        name="historico.html",
        context={"dados": dados}
    )


@app.get("/abertura-turno")
def abertura_turno_page(request: Request, usuario: str = ""):
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

    veiculo = turno_ativo[0]
    turno = turno_ativo[1]

    return templates.TemplateResponse(
        request=request,
        name="finalizar_turno.html",
        context={
            "usuario": usuario,
            "veiculo": veiculo,
            "turno": turno
        }
    )


@app.post("/finalizar-turno")
def salvar_finalizacao_turno(
    request: Request,
    usuario: str = Form(...),
    veiculo: str = Form(...),
    turno: str = Form(...),
    hodometro_final: float = Form(...),
    observacoes: str = Form("")
):
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    salvar_finalizacao_turno_db(
        data_hora=data_hora,
        usuario=usuario,
        veiculo=veiculo,
        turno=turno,
        hodometro_final=hodometro_final,
        observacoes=observacoes
    )

    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={
            "usuario": usuario,
            "mensagem": "Turno finalizado com sucesso."
        }
    )