"""Script to run evaluation against test cases."""

import argparse
import json
import sys
from pathlib import Path

from cdd_docs.config import get_settings
from cdd_docs.core.embeddings import Embedder
from cdd_docs.core.rag import RAGPipeline
from cdd_docs.core.vectorstore import VectorStore
from cdd_docs.eval.evaluator import Evaluator
from cdd_docs.eval.models import EvalCase, EvalScore


def load_cases(file_path: Path) -> list[EvalCase]:
    """Load test cases from a JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    return [
        EvalCase(
            id=case["id"],
            question=case["question"],
            expected_keywords=case.get("expected_keywords", []),
            expected_sources=case.get("expected_sources", []),
            description=case.get("description", ""),
        )
        for case in data["cases"]
    ]


def print_result(result, verbose: bool = False):
    """Print a single evaluation result."""
    # Color codes
    colors = {
        EvalScore.EXCELLENT: "\033[92m",  # Green
        EvalScore.GOOD: "\033[92m",  # Green
        EvalScore.PARTIAL: "\033[93m",  # Yellow
        EvalScore.POOR: "\033[91m",  # Red
        EvalScore.FAIL: "\033[91m",  # Red
    }
    reset = "\033[0m"
    color = colors.get(result.evaluation, "")

    print(f"\n{'='*60}")
    print(f"Case: {result.case_id}")
    print(f"Question: {result.question}")
    print(f"Score: {color}{result.evaluation.value.upper()}{reset} ({result.overall_score:.1%})")
    print(f"  Keywords: {result.keyword_score:.1%} ({len(result.keywords_found)}/{len(result.keywords_found) + len(result.keywords_missing)})")
    print(f"  Sources: {result.source_score:.1%} ({len(result.sources_found)}/{len(result.sources_found) + len(result.sources_missing)})")

    if result.keywords_missing:
        print(f"  Missing keywords: {', '.join(result.keywords_missing)}")

    if result.sources_missing:
        print(f"  Missing sources: {', '.join(result.sources_missing)}")

    if verbose:
        print(f"\nAnswer:\n{result.answer[:500]}...")
        print(f"\nSources returned: {result.sources}")


def main():
    """Run the evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate RAG quality against test cases")
    parser.add_argument(
        "cases_file",
        type=Path,
        help="Path to JSON file containing test cases",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full answers and details",
    )
    parser.add_argument(
        "--case",
        type=str,
        help="Run only a specific case by ID",
    )
    args = parser.parse_args()

    if not args.cases_file.exists():
        print(f"Error: Cases file not found: {args.cases_file}")
        sys.exit(1)

    # Load settings and initialize pipeline
    print("Initializing RAG pipeline...")
    settings = get_settings()

    vector_store = VectorStore(
        persist_directory=settings.vector_db_path,
        collection_name=settings.collection_name,
    )

    if vector_store.count() == 0:
        print("Error: Vector store is empty. Run the indexer first:")
        print("  python -m cdd_docs.scripts.index")
        sys.exit(1)

    print(f"  Vector store: {vector_store.count()} chunks")

    embedder = Embedder(model_name=settings.embedding_model)
    rag_pipeline = RAGPipeline(
        embedder=embedder,
        vector_store=vector_store,
        settings=settings,
    )

    evaluator = Evaluator(rag_pipeline)

    # Load and filter cases
    print(f"Loading cases from: {args.cases_file}")
    cases = load_cases(args.cases_file)

    if args.case:
        cases = [c for c in cases if c.id == args.case]
        if not cases:
            print(f"Error: Case '{args.case}' not found")
            sys.exit(1)

    print(f"Running {len(cases)} evaluation(s)...\n")

    # Run evaluation
    report = evaluator.evaluate_all(cases)

    # Print results
    for result in report.results:
        print_result(result, args.verbose)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total cases: {report.total_cases}")
    print(f"Passed (GOOD+): {report.passed} ({report.passed/report.total_cases:.1%})")
    print(f"Failed (POOR-): {report.failed} ({report.failed/report.total_cases:.1%})")
    print(f"Avg keyword score: {report.avg_keyword_score:.1%}")
    print(f"Avg source score: {report.avg_source_score:.1%}")
    print(f"Avg overall score: {report.avg_overall_score:.1%}")

    # Exit with error code if too many failures
    if report.failed > report.total_cases // 2:
        sys.exit(1)


if __name__ == "__main__":
    main()
