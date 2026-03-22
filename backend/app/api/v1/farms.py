from fastapi import APIRouter
from typing import List
from app.schemas.farm import FarmResponse

router = APIRouter()

@router.get("/", response_model=List[FarmResponse])
def get_farms():
    return [
        FarmResponse(
            id="f1",
            name="Lahan Jagung Utama",
            area=2.5,
            commodity="Jagung Hibrida",
            status="perhatian",
            cropPhase="Vegetatif",
            alertMessage="Indikasi serangan hama ulat grayak di blok utara."
        ),
        FarmResponse(
            id="f2",
            name="Kebun Tomat",
            area=1.0,
            commodity="Tomat Ceri",
            status="baik",
            cropPhase="Generatif"
        )
    ]
