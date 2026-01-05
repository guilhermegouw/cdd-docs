"""Evaluator for RAG quality testing."""

from cdd_docs.core.rag import RAGPipeline
from cdd_docs.eval.models import EvalCase, EvalResult, EvalReport, EvalScore


class Evaluator:
    """Evaluates RAG pipeline quality against test cases."""

    def __init__(self, rag_pipeline: RAGPipeline):
        """Initialize the evaluator.

        Args:
            rag_pipeline: The RAG pipeline to evaluate.
        """
        self.rag = rag_pipeline

    def evaluate_case(self, case: EvalCase) -> EvalResult:
        """Evaluate a single test case.

        Args:
            case: The test case to evaluate.

        Returns:
            EvalResult with scores and details.
        """
        # Get answer from RAG
        answer = self.rag.ask(case.question)

        # Extract source file paths
        source_paths = [s.file_path for s in answer.sources]

        # Check keywords (case-insensitive)
        answer_lower = answer.text.lower()
        keywords_found = [kw for kw in case.expected_keywords if kw.lower() in answer_lower]
        keywords_missing = [kw for kw in case.expected_keywords if kw.lower() not in answer_lower]

        # Check sources (partial match on path)
        sources_found = []
        sources_missing = []
        for expected in case.expected_sources:
            if any(expected in path for path in source_paths):
                sources_found.append(expected)
            else:
                sources_missing.append(expected)

        # Calculate scores
        keyword_score = (
            len(keywords_found) / len(case.expected_keywords)
            if case.expected_keywords
            else 1.0
        )
        source_score = (
            len(sources_found) / len(case.expected_sources)
            if case.expected_sources
            else 1.0
        )

        # Overall score (weighted average: keywords 70%, sources 30%)
        overall_score = (keyword_score * 0.7) + (source_score * 0.3)

        # Determine evaluation level
        if overall_score >= 0.9:
            evaluation = EvalScore.EXCELLENT
        elif overall_score >= 0.7:
            evaluation = EvalScore.GOOD
        elif overall_score >= 0.5:
            evaluation = EvalScore.PARTIAL
        elif overall_score >= 0.3:
            evaluation = EvalScore.POOR
        else:
            evaluation = EvalScore.FAIL

        return EvalResult(
            case_id=case.id,
            question=case.question,
            answer=answer.text,
            sources=source_paths,
            keywords_found=keywords_found,
            keywords_missing=keywords_missing,
            sources_found=sources_found,
            sources_missing=sources_missing,
            keyword_score=keyword_score,
            source_score=source_score,
            overall_score=overall_score,
            evaluation=evaluation,
        )

    def evaluate_all(self, cases: list[EvalCase]) -> EvalReport:
        """Evaluate all test cases and generate a report.

        Args:
            cases: List of test cases to evaluate.

        Returns:
            EvalReport with all results and summary statistics.
        """
        results = [self.evaluate_case(case) for case in cases]
        return EvalReport.from_results(results)

    def evaluate_single(self, question: str, expected_keywords: list[str] | None = None, expected_sources: list[str] | None = None) -> EvalResult:
        """Quick evaluation of a single question.

        Args:
            question: The question to ask.
            expected_keywords: Keywords expected in the answer.
            expected_sources: Source files expected.

        Returns:
            EvalResult for this question.
        """
        case = EvalCase(
            id="adhoc",
            question=question,
            expected_keywords=expected_keywords or [],
            expected_sources=expected_sources or [],
        )
        return self.evaluate_case(case)
