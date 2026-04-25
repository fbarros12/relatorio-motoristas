from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form

app = FastAPI(title="Relatório de Motoristas")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/menu")
def menu_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="menu.html"
    )


@app.get("/inspecao")
def inspecao_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="inspecao.html"
    )


@app.post("/inspecao")
def salvar_inspecao(
    request: Request,
    farois: str = Form(...),
    lanternas: str = Form(...),
    pneus: str = Form(...),
    observacoes: str = Form(...)
):
    print("INSPEÇÃO RECEBIDA:")
    print(f"Faróis: {farois}")
    print(f"Lanternas: {lanternas}")
    print(f"Pneus: {pneus}")
    print(f"Observações: {observacoes}")

    return templates.TemplateResponse(
        request=request,
        name="menu.html"
    )