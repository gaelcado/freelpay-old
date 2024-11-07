from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, user, invoice
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Désactiver les logs de debug des bibliothèques externes
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("python_multipart").setLevel(logging.WARNING)

load_dotenv()

app = FastAPI()

# Configurez CORS et autres middlewares ici
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://frontend:3000", 
        "https://freelpay-nextjs-pm2fo.ondigitalocean.app",
        "https://freelpay.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# Configurez la taille maximale du corps de la requête à 10 Mo
app.max_request_size = 10 * 1024 * 1024  # 10 Mo en octets

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(invoice.router, prefix="/invoices", tags=["invoices"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)