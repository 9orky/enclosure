from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuildTerm:
    name: str
    description: str


GUILD_GLOSSARY: tuple[GuildTerm, ...] = (
    GuildTerm(
        "Charter",
        "The local agreement for this repository: roots, boundaries, flow, shape, "
        "and the checks that prove work stayed inside them.",
    ),
    GuildTerm(
        "Lore",
        "The rule path an agent reads before touching the work. Lore turns scattered "
        "project memory into explicit guidance.",
    ),
    GuildTerm(
        "Plumb",
        "The discovery pass before planning or edits. Plumb finds ownership, seams, "
        "dependency direction, risk, and the right checks.",
    ),
    GuildTerm(
        "Ledger",
        "The receipt from Plumb: what was read, why it was read, where the agent "
        "stops, and which checks must run afterward.",
    ),
    GuildTerm(
        "Pattern",
        "A known-good project shape captured for repeatable work, so agents create "
        "modules from local precedent instead of improvising.",
    ),
    GuildTerm(
        "Trial Fit",
        "A no-write preview of the paths a Pattern would place. It answers what "
        "would change before anything is created.",
    ),
    GuildTerm(
        "Bench Preview",
        "A no-write rendering of the Pattern tree and skeleton files. It lays the "
        "shape on the bench so conventions are visible before implementation.",
    ),
    GuildTerm(
        "Inspection",
        "The check pass before and after work. Inspection reports whether the "
        "Charter, Lore, boundaries, shape, and Pattern still hold.",
    ),
    GuildTerm(
        "Warp",
        "A place where implementation shape bends away from the declared Pattern or "
        "agreement. Warp is a signal to fix or ask for Signoff.",
    ),
    GuildTerm(
        "Signoff",
        "The human approval point before changing the agreement, widening a seam, "
        "or treating discovered Warp as intentional.",
    ),
)


__all__ = ["GUILD_GLOSSARY", "GuildTerm"]
