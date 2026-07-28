import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agent.tax_tools import embed_text
from src.models.tax_rules_document import TaxRulesDocument
from src.models.tax_rules_document_chunk import TaxRulesDocumentChunk


class NotFoundError(Exception):
    pass


def _chunk_text(content: str) -> list[str]:
    # Paragraph-sized chunks (split on blank lines) — precise citations
    # over whole-document embeddings (research.md).
    raw_chunks = re.split(r"\n\s*\n", content.strip())
    return [chunk.strip() for chunk in raw_chunks if chunk.strip()]


async def add_document(session: AsyncSession, title: str, content: str) -> TaxRulesDocument:
    document = TaxRulesDocument(title=title, content=content)
    session.add(document)
    await session.flush()

    for index, chunk_text in enumerate(_chunk_text(content)):
        session.add(
            TaxRulesDocumentChunk(
                document_id=document.id,
                chunk_index=index,
                chunk_text=chunk_text,
                embedding=await embed_text(chunk_text),
            )
        )
    await session.commit()
    return await get_document(session, document.id)


async def get_document(session: AsyncSession, document_id: uuid.UUID) -> TaxRulesDocument:
    stmt = (
        select(TaxRulesDocument)
        .where(TaxRulesDocument.id == document_id)
        .options(selectinload(TaxRulesDocument.chunks))
    )
    document = (await session.execute(stmt)).scalar_one_or_none()
    if document is None:
        raise NotFoundError(f"No tax rules document with id {document_id}")
    return document


async def list_documents(session: AsyncSession) -> list[TaxRulesDocument]:
    stmt = (
        select(TaxRulesDocument)
        .options(selectinload(TaxRulesDocument.chunks))
        .order_by(TaxRulesDocument.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> None:
    document = await get_document(session, document_id)
    await session.delete(document)
    await session.commit()
