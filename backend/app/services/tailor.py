"""Service module for compiling tailored resume drafts."""

from app.schemas.optimization import OptimizationResult


def apply_selected_suggestions(
    original_resume_text: str,
    optimization_result: OptimizationResult,
    selected_indices: list[int],
) -> str:
    """Replaces original text fragments with accepted suggestions in the original resume text."""
    tailored_text = original_resume_text
    valid_indices = set(selected_indices)

    for idx, suggestion in enumerate(optimization_result.suggestions):
        if idx in valid_indices and suggestion.original_text:
            if suggestion.original_text in tailored_text:
                tailored_text = tailored_text.replace(
                    suggestion.original_text, suggestion.suggested_text, 1
                )

    return tailored_text