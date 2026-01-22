from fastapi import APIRouter

router = APIRouter()

@router.get("/")
@router.get("/healthz/")
@router.get("/healthz")
def healthz():
    return {"ok": True}
