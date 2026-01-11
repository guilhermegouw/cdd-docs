"""Mermaid diagram validation using the official mermaid-cli."""

import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Regex to extract mermaid code blocks from markdown
MERMAID_BLOCK_PATTERN = re.compile(
    r"```mermaid\n(.*?)```",
    re.DOTALL,
)


@dataclass
class MermaidError:
    """A mermaid validation error."""

    diagram_index: int
    diagram_code: str
    error_message: str


def extract_mermaid_blocks(text: str) -> list[str]:
    """Extract all mermaid code blocks from markdown text.

    Args:
        text: Markdown text that may contain mermaid blocks.

    Returns:
        List of mermaid diagram code strings.
    """
    return MERMAID_BLOCK_PATTERN.findall(text)


def validate_mermaid(code: str) -> str | None:
    """Validate a mermaid diagram using mmdc CLI.

    Args:
        code: The mermaid diagram code to validate.

    Returns:
        None if valid, or error message string if invalid.
    """
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=True
        ) as tmp_out:
            result = subprocess.run(
                ["mmdc", "-i", "-", "-o", tmp_out.name],
                input=code,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # Extract the meaningful error from stderr
                error = result.stderr or result.stdout
                # Clean up the error message - extract just the parse error
                if "Error:" in error:
                    error_lines = []
                    capturing = False
                    for line in error.split("\n"):
                        if line.strip().startswith("Error:"):
                            capturing = True
                        if capturing:
                            if line.strip().startswith("at ") or line.strip().startswith(
                                "Parser"
                            ):
                                break
                            error_lines.append(line)
                    return "\n".join(error_lines).strip()
                return error.strip()

            return None

    except subprocess.TimeoutExpired:
        return "Validation timed out"
    except FileNotFoundError:
        logger.warning("mmdc CLI not found - skipping mermaid validation")
        return None
    except Exception as e:
        logger.error(f"Mermaid validation error: {e}")
        return None


def validate_all_mermaid(text: str) -> list[MermaidError]:
    """Validate all mermaid blocks in a markdown text.

    Args:
        text: Markdown text that may contain mermaid blocks.

    Returns:
        List of MermaidError objects for any invalid diagrams.
    """
    blocks = extract_mermaid_blocks(text)
    errors = []

    for i, block in enumerate(blocks):
        error = validate_mermaid(block)
        if error:
            errors.append(
                MermaidError(
                    diagram_index=i + 1,
                    diagram_code=block,
                    error_message=error,
                )
            )

    return errors


def format_errors_for_llm(errors: list[MermaidError]) -> str:
    """Format mermaid errors as a prompt for the LLM to fix.

    Args:
        errors: List of MermaidError objects.

    Returns:
        Formatted string describing the errors.
    """
    parts = ["The following mermaid diagrams have syntax errors:\n"]

    for error in errors:
        parts.append(f"Diagram {error.diagram_index}:")
        parts.append(f"```mermaid\n{error.diagram_code}```")
        parts.append(f"Error: {error.error_message}\n")

    parts.append(
        "Please fix the syntax errors in these diagrams and provide the corrected "
        "version of your complete response."
    )

    return "\n".join(parts)
