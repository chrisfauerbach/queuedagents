from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models import Prompt
from backend.app.schemas import PromptCreate, PromptUpdate, PromptResponse

router = APIRouter()


@router.post("/prompts", response_model=PromptResponse, status_code=201)
async def create_prompt(
    payload: PromptCreate, session: AsyncSession = Depends(get_session)
):
    prompt = Prompt(
        name=payload.name,
        prompt=payload.prompt,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    session.add(prompt)
    await session.commit()
    await session.refresh(prompt)
    return prompt


@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Prompt).order_by(Prompt.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Prompt).where(Prompt.id == prompt_id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.put("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    payload: PromptUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Prompt).where(Prompt.id == prompt_id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prompt, field, value)

    await session.commit()
    await session.refresh(prompt)
    return prompt


@router.delete("/prompts/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Prompt).where(Prompt.id == prompt_id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    await session.delete(prompt)
    await session.commit()
    return Response(status_code=204)
