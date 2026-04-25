"""Authentication routes — login, register, session."""
from fastapi import APIRouter, HTTPException
from models import LoginRequest, RegisterRequest
from supabase_client import get_supabase

router = APIRouter()

@router.post("/login", summary="Sign in with email/password")
async def login(req: LoginRequest):
    sb = get_supabase()
    try:
        resp = sb.auth.sign_in_with_password({"email": req.email, "password": req.password})
        user = resp.user
        session = resp.session
        # Fetch role from public.users
        udata = sb.table("users").select("role, username").ilike("username", req.email.split("@")[0]).limit(1).execute().data
        role = udata[0]["role"] if udata else user.user_metadata.get("role", "patient")
        name = udata[0]["username"] if udata else user.user_metadata.get("username", req.email.split("@")[0])
        return {
            "access_token": session.access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": role,
            "username": name,
            "email": user.email
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@router.post("/register", summary="Create new account")
async def register(req: RegisterRequest):
    sb = get_supabase()
    try:
        resp = sb.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {"data": {"username": req.username, "role": req.role}}
        })
        sb.table("users").insert({"username": req.username, "password_hash": "***", "role": req.role}).execute()
        return {"success": True, "message": "Account created. Check your email to confirm."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout", summary="Sign out")
async def logout(token: str):
    sb = get_supabase()
    try:
        sb.auth.sign_out()
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/me", summary="Get current user info")
async def get_me(token: str):
    sb = get_supabase()
    try:
        user = sb.auth.get_user(token).user
        return {"user_id": user.id, "email": user.email, "role": user.user_metadata.get("role"), "username": user.user_metadata.get("username")}
    except Exception as e:
        raise HTTPException(401, "Invalid token")
