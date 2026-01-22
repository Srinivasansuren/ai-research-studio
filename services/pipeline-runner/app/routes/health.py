from fastapi import APIRouter

router = APIRouter()

#@router.get("/healthz")
@router.get("/healthz/")
@router.get("/")
def health():
    return {"status": "ok"}

