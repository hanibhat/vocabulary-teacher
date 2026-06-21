import logging

from fastapi import APIRouter, HTTPException

from services.vocabulary import get_vocabulary

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/vocabulary")
def read_vocabulary():
    try:
        return get_vocabulary()
    except Exception as error:
        logger.exception("Unexpected vocabulary error: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error
