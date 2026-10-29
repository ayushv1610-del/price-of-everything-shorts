"""Deterministic, review-first production queue. No network or publishing."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Scene:
    seconds: int
    narration: str
    visual_direction: str

@dataclass(frozen=True)
class ShortPlan:
    title: str
    hook: str
    scenes: tuple[Scene, ...]
    fact_check_required: bool = True
    publishing_approved: bool = False

def validate_plan(plan: ShortPlan) -> list[str]:
    issues = []
    if not 12 <= sum(s.seconds for s in plan.scenes) <= 60:
        issues.append("Short duration must be 12-60 seconds")
    if not 3 <= len(plan.scenes) <= 12:
        issues.append("Use 3-12 distinct scenes")
    if len(plan.hook.strip()) < 12:
        issues.append("Hook is too short")
    if len(plan.title) > 100:
        issues.append("Title exceeds 100 characters")
    if any(not s.narration.strip() or not s.visual_direction.strip() for s in plan.scenes):
        issues.append("Every scene requires narration and visual direction")
    if not plan.fact_check_required:
        issues.append("Research verification must remain enabled")
    if plan.publishing_approved:
        issues.append("Draft generator must not grant publishing approval")
    return issues

def sample_plan() -> ShortPlan:
    return ShortPlan(
        title="Why luxury packaging changes what we think",
        hook="Can a box make a product feel more expensive?",
        scenes=(
            Scene(5, "Can a box make a product feel more expensive?", "Macro shot of two contrasting unbranded boxes"),
            Scene(7, "Packaging creates expectations before we even touch what's inside.", "Original motion graphic of anticipation"),
            Scene(7, "Weight, texture and presentation can shape how we perceive quality.", "Close-ups of material and texture, licensed footage only"),
            Scene(7, "But an expensive-looking box doesn't prove the product is better.", "Simple comparison with no misleading product claims"),
            Scene(5, "Next time you shop, notice what the packaging makes you assume.", "Question on screen with original geometric animation"),
        )
    )
