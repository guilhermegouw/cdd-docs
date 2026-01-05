"""FastAPI endpoints for evaluation."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cdd_docs.config import get_settings
from cdd_docs.core.embeddings import Embedder
from cdd_docs.core.rag import RAGPipeline
from cdd_docs.core.vectorstore import VectorStore
from cdd_docs.eval.evaluator import Evaluator
from cdd_docs.eval.models import EvalCase

app = FastAPI(
    title="CDD Docs Evaluation API",
    description="API for evaluating RAG quality on CDD documentation",
    version="0.1.0",
)

# Global instances
_rag_pipeline: RAGPipeline | None = None
_evaluator: Evaluator | None = None


def get_evaluator() -> Evaluator:
    """Get or create the evaluator instance."""
    global _rag_pipeline, _evaluator

    if _evaluator is None:
        settings = get_settings()

        vector_store = VectorStore(
            persist_directory=settings.vector_db_path,
            collection_name=settings.collection_name,
        )

        if vector_store.count() == 0:
            raise HTTPException(
                status_code=503,
                detail="Vector store is empty. Run the indexer first.",
            )

        embedder = Embedder(model_name=settings.embedding_model)

        _rag_pipeline = RAGPipeline(
            embedder=embedder,
            vector_store=vector_store,
            settings=settings,
        )

        _evaluator = Evaluator(_rag_pipeline)

    return _evaluator


# Request/Response models
class AskRequest(BaseModel):
    """Request to ask a question."""

    question: str


class AskResponse(BaseModel):
    """Response from asking a question."""

    answer: str
    sources: list[dict]


class EvalRequest(BaseModel):
    """Request to evaluate a single question."""

    question: str
    expected_keywords: list[str] = []
    expected_sources: list[str] = []


class EvalResponse(BaseModel):
    """Response from evaluation."""

    case_id: str
    question: str
    answer: str
    sources: list[str]
    keywords_found: list[str]
    keywords_missing: list[str]
    sources_found: list[str]
    sources_missing: list[str]
    keyword_score: float
    source_score: float
    overall_score: float
    evaluation: str


class BatchEvalRequest(BaseModel):
    """Request to evaluate multiple test cases."""

    cases: list[EvalCase]


class BatchEvalResponse(BaseModel):
    """Response from batch evaluation."""

    total_cases: int
    passed: int
    failed: int
    avg_keyword_score: float
    avg_source_score: float
    avg_overall_score: float
    results: list[EvalResponse]


# Endpoints
@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Ask a question and get an answer with sources."""
    evaluator = get_evaluator()
    answer = evaluator.rag.ask(request.question)

    return AskResponse(
        answer=answer.text,
        sources=[
            {
                "file_path": s.file_path,
                "section": s.section,
                "score": s.score,
            }
            for s in answer.sources
        ],
    )


@app.post("/eval", response_model=EvalResponse)
def evaluate(request: EvalRequest):
    """Evaluate a single question against expected criteria."""
    evaluator = get_evaluator()

    result = evaluator.evaluate_single(
        question=request.question,
        expected_keywords=request.expected_keywords,
        expected_sources=request.expected_sources,
    )

    return EvalResponse(
        case_id=result.case_id,
        question=result.question,
        answer=result.answer,
        sources=result.sources,
        keywords_found=result.keywords_found,
        keywords_missing=result.keywords_missing,
        sources_found=result.sources_found,
        sources_missing=result.sources_missing,
        keyword_score=result.keyword_score,
        source_score=result.source_score,
        overall_score=result.overall_score,
        evaluation=result.evaluation.value,
    )


@app.post("/eval/batch", response_model=BatchEvalResponse)
def evaluate_batch(request: BatchEvalRequest):
    """Evaluate multiple test cases and get a summary report."""
    evaluator = get_evaluator()
    report = evaluator.evaluate_all(request.cases)

    return BatchEvalResponse(
        total_cases=report.total_cases,
        passed=report.passed,
        failed=report.failed,
        avg_keyword_score=report.avg_keyword_score,
        avg_source_score=report.avg_source_score,
        avg_overall_score=report.avg_overall_score,
        results=[
            EvalResponse(
                case_id=r.case_id,
                question=r.question,
                answer=r.answer,
                sources=r.sources,
                keywords_found=r.keywords_found,
                keywords_missing=r.keywords_missing,
                sources_found=r.sources_found,
                sources_missing=r.sources_missing,
                keyword_score=r.keyword_score,
                source_score=r.source_score,
                overall_score=r.overall_score,
                evaluation=r.evaluation.value,
            )
            for r in report.results
        ],
    )


# For running directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
