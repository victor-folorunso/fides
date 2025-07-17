from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from tortoise.contrib.fastapi import register_tortoise
from pathlib import Path
from dotenv import load_dotenv
import httpx, jwt, time, os
from backend.models import AirdropClaim, VaultRequest, VaultStake

# ────── Base Directories and Env ──────
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
 
load_dotenv()
CLIENT_ID = os.getenv("WLD_CLIENT_ID")
CLIENT_SECRET = os.getenv("WLD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
PRIVATE_KEY = os.getenv("WORLDCOIN_APP_PRIVATE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt")

# ────── FastAPI App ──────
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key")

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# ────── Static Files ──────
app.mount("/style", StaticFiles(directory=FRONTEND_DIR / "style"), name="style")
app.mount("/scripts", StaticFiles(directory=FRONTEND_DIR / "scripts"), name="scripts")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

# ────── HTML Pages ──────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not request.session.get("verified"):
        return RedirectResponse("/login")
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/vault", response_class=HTMLResponse)
async def vault_page(request: Request):
    if not request.session.get("verified"):
        return RedirectResponse("/login")
    return FileResponse(FRONTEND_DIR / "vault.html")

@app.get("/swap", response_class=HTMLResponse)
async def vault_page(request: Request):
    if not request.session.get("verified"):
        return RedirectResponse("/login")
    return FileResponse(FRONTEND_DIR / "swap.html")

@app.get("/airdrop", response_class=HTMLResponse)
async def vault_page(request: Request):
    if not request.session.get("verified"):
        return RedirectResponse("/login")
    return FileResponse(FRONTEND_DIR / "airdrop.html")

@app.get("/login")
async def login():
    return RedirectResponse(
        f"https://id.worldcoin.org/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid"
    )
  
@app.get("/callback")
async def callback(request: Request, code: str = None):
    print("🔁 Callback params:", dict(request.query_params))

    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://id.worldcoin.org/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI
            },  
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )     
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Token exchange failed")

        access_token = token_resp.json().get("access_token")
        userinfo_resp = await client.get(
            "https://id.worldcoin.org/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Userinfo fetch failed")

        userinfo = userinfo_resp.json()
        request.session["verified"] = True
        request.session["user"] = userinfo

    #return RedirectResponse("/")
    return HTMLResponse("<h1>Hello, World!</h1>")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

# ────── Airdrop Claim ──────
@app.post("/api/claim")
async def claim_airdrop(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not verified")
    wallet_address = user.get("sub")

    existing = await AirdropClaim.get_or_none(wallet_address=wallet_address)
    if existing and existing.claimed:
        return {"message": "Already claimed"}

    if not existing:
        await AirdropClaim.create(wallet_address=wallet_address, claimed=True)
    else:
        existing.claimed = True
        await existing.save()

    payload = {
        "to": wallet_address,
        "token": "FIDES",
        "amount": "100000000",
        "chain": "worldchain",
        "exp": int(time.time()) + 60
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"message": "Claim ready", "signed_claim": jwt_token}

# ────── Vault Request ──────
@app.post("/api/vault")
async def vault_request(request: Request, payload: dict = Body(...)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not verified")

    wallet_address = user.get("sub")
    amount = payload.get("amount")
    duration = payload.get("duration")

    if not wallet_address or not amount or not duration:
        raise HTTPException(status_code=400, detail="Missing parameters")

    await VaultRequest.create(wallet_address=wallet_address, amount=amount, duration=duration, claimed=False)

    jwt_payload = {
        "sub": wallet_address,
        "amount": str(amount),
        "transaction": "vault",
        "duration": int(duration),
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
        "app_id": CLIENT_ID,
    }

    signed_jwt = jwt.encode(jwt_payload, PRIVATE_KEY, algorithm="RS256")
    return {"message": "Vault request prepared", "signed_claim": signed_jwt}

# ────── Vault Confirmation ──────
@app.post("/api/vault/confirm")
async def confirm_vault_tx(request: Request, payload: dict = Body(...)):
    tx_hash = payload.get("tx_hash")
    if not tx_hash:
        raise HTTPException(status_code=400, detail="Missing tx_hash")

    user = request.session.get("user")
    wallet_address = user.get("sub")

    req = await VaultRequest.get_or_none(wallet_address=wallet_address, claimed=False)
    if not req:
        raise HTTPException(status_code=404, detail="No pending vault found")

    matured_on = int(time.time()) + int(req.duration) * 30 * 24 * 3600  # rough calc
    await VaultStake.create(wallet_address=wallet_address, amount=req.amount, duration=req.duration, tx_hash=tx_hash, matured_on=matured_on)
    await req.delete()

    return {"message": "Vault confirmed and stored"}

# ────── List Completed Stakes ──────
@app.get("/api/completed-stakes")
async def completed_stakes(request: Request):
    user = request.session.get("user")
    wallet_address = user.get("sub")

    now = int(time.time())
    stakes = await VaultStake.filter(wallet_address=wallet_address, claimed=False).filter(matured_on__lte=now)
    return {"stakes": [stake.dict() for stake in stakes]}

# ────── Claim Stake ──────
@app.post("/api/claim-stake/{stake_id}")
async def claim_stake(stake_id: int, request: Request):
    user = request.session.get("user")
    wallet_address = user.get("sub")

    stake = await VaultStake.get_or_none(id=stake_id, wallet_address=wallet_address, claimed=False)
    if not stake or int(time.time()) < stake.matured_on:
        raise HTTPException(status_code=400, detail="Not matured or not found")

    stake.claimed = True
    await stake.save()
    return {"message": "Stake claimed successfully"}

# ────── DB Init ──────
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["backend.models"]},  # ✅ FIXED: use full import path
    generate_schemas=True,
    add_exception_handlers=True,
)

 