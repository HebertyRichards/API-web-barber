from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routes.agendamento import agendamento_router
from routes.servicos_realizados import servico_router

load_dotenv()

cliente_app = os.getenv("FRONTEND_URL", "").split(",")

app = FastAPI(
    title="API Barbearia",
    description="API para gestão de agendamentos da barbearia.",
    version="1.0.0"
)

app.include_router(agendamento_router)
app.include_router(servico_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cliente_app,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
