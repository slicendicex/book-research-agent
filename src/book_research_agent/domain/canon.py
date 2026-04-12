from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainPack:
    name: str
    instructions: tuple[str, ...]
    terminology: tuple[str, ...]


DEFAULT_DOMAIN_PACK = DomainPack(
    name="book-project-canon",
    instructions=(
        "Interpret retrieved evidence through the book project's canon-aware lens.",
        "Prefer wording that distinguishes supported canon from interpretation.",
        "Do not add unsupported canon beyond the retrieved sources.",
    ),
    terminology=(
        "Auditor",
        "Old Man",
        "Museum",
        "Forest",
        "preservation",
        "life",
        "order",
        "chaos",
        "canon",
    ),
)


def format_domain_guidance(domain_pack: DomainPack) -> str:
    instruction_lines = [f"- {instruction}" for instruction in domain_pack.instructions]
    terms = ", ".join(domain_pack.terminology)
    return "\n".join(
        [
            "Domain guidance:",
            f"name: {domain_pack.name}",
            "instructions:",
            *instruction_lines,
            f"terminology: {terms}",
        ]
    )
