from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import os

app = FastAPI(title="Techra API")

# === ENV variabler (lägg i App Service) ===
TENANT_ID = os.getenv("AZURE_TENANT_ID")
API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID")

# Grupp → Roll mapping (byt GUIDs mot riktiga Object IDs från Entra)
GROUP_TO_ROLE = {
    "d5f7f6e7-380f-468d-9d0e-6a7c30fd3ef9": "app-techra-supervisor",
    "5dc860e3-600d-4332-9200-5cdc53e7242b": "app-techra-technician",
    "04889f68-70f8-4848-9a7a-9ca3cd1c8864": "app-techra-viewer",
}

# Token verifiering
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    try:
        claims = jwt.get_unverified_claims(token)

        # Kontrollera audience
        if claims.get("aud") != API_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Invalid audience")

        return claims
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# === MODELLER ===
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


# === ENDPOINTS ===
@app.get("/")
def root():
    return {"message": "🚀 Techra API is running!"}


@app.get("/me")
def get_me(claims: dict = Depends(verify_token)):
    tenant_id = claims.get("tid")
    groups = claims.get("groups", [])
    roles = [GROUP_TO_ROLE[g] for g in groups if g in GROUP_TO_ROLE]

    return {
        "tenant_id": tenant_id,
        "roles": roles,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, claims: dict = Depends(verify_token)):
    """
    Placeholder för felsökningschatten.
    Just nu returneras ett demo-svar.
    Senare kopplas detta mot Azure OpenAI + Search.
    """
    question = req.question

    # Placeholder-svar
    answer = f"Du frågade: '{question}'. Just nu kör vi demo-svar."
    sources = ["manual.pdf", "service_log_2025-09-05.json"]

    return ChatResponse(answer=answer, sources=sources)
