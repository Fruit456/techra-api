from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
import httpx

app = FastAPI(title="Techra API")

# === ENV variabler (lägg i Azure App Service → Konfig) ===
TENANT_ID = os.getenv("AZURE_TENANT_ID")
API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID")
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT")        # ex: https://aoai-techra.openai.azure.com
AOAI_KEY = os.getenv("AOAI_KEY")
AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT")    # ex: gpt-4o-mini

# Grupp → Roll mapping (byt ut GUIDs mot riktiga Object IDs från Entra)
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

# === Routes ===

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


@app.post("/chat")
async def chat(
    body: dict = Body(...),
    claims: dict = Depends(verify_token)
):
    """
    Enkel chatt-endpoint som skickar prompten till Azure OpenAI
    """
    user_message = body.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Bygg AOAI request
    url = f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_DEPLOYMENT}/chat/completions?api-version=2024-05-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": AOAI_KEY,
    }
    payload = {
        "messages": [
            {"role": "system", "content": "Du är Techra AI och hjälper till med felsökning av tåg."},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"AOAI error: {r.text}")
        data = r.json()

    reply = data["choices"][0]["message"]["content"]

    return {
        "user": user_message,
        "reply": reply,
    }
