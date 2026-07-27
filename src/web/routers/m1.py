"""M1 rule extraction demo API."""

from fastapi import APIRouter

from biz.m1_service import M1ExtractionRequest, M1ReviewRequest, get_m1_service


router = APIRouter()


@router.get("/sample")
async def sample_document():
    """Return the built-in M1 demo document."""
    return {"status": "success", "sample": get_m1_service().sample_document()}


@router.post("/extract")
async def extract_rules(request: M1ExtractionRequest):
    """Run the local M1 extraction baseline."""
    return get_m1_service().extract(request)


@router.post("/review")
async def review_rule(request: M1ReviewRequest):
    """Apply an in-memory human review decision."""
    return get_m1_service().review(request)
