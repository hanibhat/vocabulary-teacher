import logging

from fastapi import APIRouter, HTTPException

from services.vocabulary import VocabularyConfigError, VocabularyFetchError, make_vocabulary


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/vocabulary")
def read_vocabulary():
    try:
        return make_vocabulary()
    except VocabularyConfigError as error:
        logger.exception("Vocabulary configuration error: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error
    except VocabularyFetchError as error:
        logger.exception("Vocabulary fetch error: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error
