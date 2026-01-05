"""Data models for evaluation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EvalScore(str, Enum):
    """Evaluation score levels."""

    EXCELLENT = "excellent"  # Answer is complete and accurate
    GOOD = "good"  # Answer is mostly correct, minor gaps
    PARTIAL = "partial"  # Answer has some correct info but missing key points
    POOR = "poor"  # Answer is mostly wrong or irrelevant
    FAIL = "fail"  # No answer or completely wrong


@dataclass
class EvalCase:
    """A single evaluation test case.

    Attributes:
        id: Unique identifier for the test case
        question: The question to ask the RAG system
        expected_keywords: Keywords that should appear in a good answer
        expected_sources: File paths that should be in the sources
        description: Human-readable description of what this tests
    """

    id: str
    question: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_sources: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class EvalResult:
    """Result of evaluating a single test case.

    Attributes:
        case_id: ID of the test case
        question: The question asked
        answer: The RAG system's answer
        sources: Sources returned by RAG
        keywords_found: Which expected keywords were found
        keywords_missing: Which expected keywords were missing
        sources_found: Which expected sources were found
        sources_missing: Which expected sources were missing
        keyword_score: Percentage of keywords found (0-1)
        source_score: Percentage of sources found (0-1)
        overall_score: Combined score
        evaluation: Human-readable evaluation
        timestamp: When the evaluation was run
    """

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
    evaluation: EvalScore
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvalReport:
    """Summary report of an evaluation run.

    Attributes:
        results: Individual test results
        total_cases: Number of test cases
        passed: Number of cases with GOOD or EXCELLENT score
        failed: Number of cases with POOR or FAIL score
        avg_keyword_score: Average keyword score
        avg_source_score: Average source score
        avg_overall_score: Average overall score
        timestamp: When the report was generated
    """

    results: list[EvalResult]
    total_cases: int
    passed: int
    failed: int
    avg_keyword_score: float
    avg_source_score: float
    avg_overall_score: float
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_results(cls, results: list[EvalResult]) -> "EvalReport":
        """Create a report from a list of results."""
        if not results:
            return cls(
                results=[],
                total_cases=0,
                passed=0,
                failed=0,
                avg_keyword_score=0.0,
                avg_source_score=0.0,
                avg_overall_score=0.0,
            )

        passed = sum(
            1 for r in results if r.evaluation in (EvalScore.EXCELLENT, EvalScore.GOOD)
        )
        failed = sum(
            1 for r in results if r.evaluation in (EvalScore.POOR, EvalScore.FAIL)
        )

        return cls(
            results=results,
            total_cases=len(results),
            passed=passed,
            failed=failed,
            avg_keyword_score=sum(r.keyword_score for r in results) / len(results),
            avg_source_score=sum(r.source_score for r in results) / len(results),
            avg_overall_score=sum(r.overall_score for r in results) / len(results),
        )
