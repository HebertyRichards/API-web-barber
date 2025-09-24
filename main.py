from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routes.agendamento import agendamento_router

# Carregar variáveis do .env
load_dotenv()

# Ler a variável do .env
cliente_app = os.getenv("FRONTEND_URL", "").split(",")

app = FastAPI(
    title="API Barbearia",
    description="API para gestão de agendamentos da barbearia.",
    version="1.0.0"
)

app.include_router(agendamento_router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bem-vindo à API da Barbearia"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=cliente_app,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
