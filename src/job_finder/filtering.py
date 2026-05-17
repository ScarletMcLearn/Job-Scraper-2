from __future__ import annotations

import re
from dataclasses import dataclass

from job_finder.config import FilterConfig
from job_finder.models import JobMatch, JobPost, MatchStatus


@dataclass(frozen=True)
class PatternRule:
    label: str
    pattern: re.Pattern[str]


def _rule(label: str, pattern: str) -> PatternRule:
    return PatternRule(label, re.compile(pattern, re.IGNORECASE | re.MULTILINE))


ROLE_RULES = [
    _rule("QA", r"\bq\.?a\.?\b|\bquality analyst\b"),
    _rule("Test", r"\btest(?:ing|er|ers)?\b|\bsoftware tester\b"),
    _rule("SQA", r"\bs\.?q\.?a\.?\b|\bsoftware quality assurance\b"),
    _rule("SDET", r"\bsdet\b|\bsoftware development engineer(?:s)? in test\b"),
    _rule("Quality Assurance", r"\bquality assurance\b"),
    _rule("Automation", r"\bautomation\b|\bautomated test(?:ing)?\b"),
    _rule("Selenium", r"\bselenium\b"),
    _rule("Cypress", r"\bcypress\b"),
    _rule("Playwright", r"\bplaywright\b"),
]

TITLE_ROLE_RULES = [
    _rule("QA", r"\bq\.?a\.?\b"),
    _rule("SQA", r"\bs\.?q\.?a\.?\b|\bsoftware quality assurance\b"),
    _rule("SDET", r"\bsdet\b|\bsoftware development engineer(?:s)? in test\b"),
    _rule("Quality Assurance", r"\bquality assurance\b"),
    _rule("Test", r"\b(?:software )?test(?:ing)? (?:engineer|analyst|specialist|lead|manager)\b|\bsoftware tester\b|\btester\b"),
    _rule("Automation", r"\b(?:qa|test) automation\b|\bautomation (?:qa|test|tester)\b"),
    _rule("Selenium", r"\bselenium\b"),
    _rule("Cypress", r"\bcypress\b"),
    _rule("Playwright", r"\bplaywright\b"),
]

SUPPORT_POSITIVE_RULES = [
    _rule("visa sponsorship", r"\bvisa sponsorship\b|\bsponsor(?:ing)? visa\b|\bvisa support\b"),
    _rule("work authorization support", r"\bwork authorization support\b|\bimmigration support\b"),
    _rule("relocation support", r"\brelocation (?:support|assistance|package)\b|\brelocat(?:e|ion) assistance\b"),
    _rule("international relocation", r"\binternational relocation\b|\bglobal mobility\b"),
]

SUPPORT_NEGATIVE_RULES = [
    _rule("no visa sponsorship", r"\bno (?:visa )?sponsorship\b|\bno visa sponsor(?:ship)?\b"),
    _rule("unable to sponsor", r"\bunable to sponsor\b|\bcannot sponsor\b|\bcan't sponsor\b|\bwill not sponsor\b"),
    _rule("no relocation", r"\bno relocation\b|\brelocation (?:is )?not (?:provided|available|offered)\b"),
    _rule("existing work authorization required", r"\bmust (?:already )?(?:be )?authorized to work\b|\bright to work (?:is )?required\b"),
]

REMOTE_RULES = [
    _rule("remote", r"\bremote\b|\bwork from home\b|\bdistributed team\b"),
    _rule("work from anywhere", r"\bwork from anywhere\b|\banywhere in the world\b"),
]

REMOTE_ELIGIBLE_RULES = [
    _rule("Bangladesh eligible", r"\bbangladesh\b|\bbangladeshi\b|\bdhaka\b"),
    _rule("worldwide remote", r"\bworldwide\b|\bglobally\b|\bglobal remote\b|\banywhere in the world\b|\bwork from anywhere\b"),
    _rule("Asia/APAC remote", r"\bapac\b|\basia(?:-pacific)?\b|\bsouth asia\b"),
    _rule("UTC+6 compatible", r"\butc\s*\+?\s*0?6\b|\bgmt\s*\+?\s*0?6\b"),
]

REMOTE_RESTRICTION_RULES = [
    _rule("US-only remote", r"\b(?:u\.?s\.?|united states|usa)[ -]?only\b|\bonly (?:in|within) (?:the )?(?:u\.?s\.?|united states|usa)\b"),
    _rule("Canada-only remote", r"\bcanada[ -]?only\b|\bonly (?:in|within) canada\b"),
    _rule("UK-only remote", r"\b(?:u\.?k\.?|united kingdom)[ -]?only\b|\bonly (?:in|within) (?:the )?(?:u\.?k\.?|united kingdom)\b"),
    _rule("Europe-only remote", r"\b(?:eu|europe|emea)[ -]?only\b|\bonly (?:in|within) (?:the )?(?:eu|europe|emea)\b"),
    _rule("LATAM-only remote", r"\blatam[ -]?only\b|\bonly (?:in|within) latam\b"),
    _rule("must be based elsewhere", r"\bmust be based in (?!bangladesh\b)[a-z ,.-]+"),
]


class JobClassifier:
    def __init__(self, config: FilterConfig | None = None) -> None:
        self.config = config or FilterConfig()

    def classify(self, job: JobPost) -> JobMatch:
        text = _normalize_text(job.searchable_text())
        title_text = _normalize_text(job.title)
        full_text_role_matches = _labels_for_rules(ROLE_RULES, text)
        title_role_matches = _labels_for_rules(TITLE_ROLE_RULES, title_text)
        if not title_role_matches:
            reason = "role keyword mismatch"
            if full_text_role_matches:
                reason = "role keyword only found outside title"
            return JobMatch(
                job=job,
                status=MatchStatus.EXCLUDED,
                matched_keywords=full_text_role_matches,
                reasons=[reason],
            )
        role_matches = _dedupe(title_role_matches + full_text_role_matches)

        positive_support = _labels_for_rules(SUPPORT_POSITIVE_RULES, text)
        negative_support = _labels_for_rules(SUPPORT_NEGATIVE_RULES, text)
        positive_support = _remove_negated_support(positive_support, negative_support)
        remote_markers = _labels_for_rules(REMOTE_RULES, text)
        remote_eligible = _labels_for_rules(REMOTE_ELIGIBLE_RULES, text)
        remote_restrictions = _labels_for_rules(REMOTE_RESTRICTION_RULES, text)
        remote_flag = bool(job.remote)

        evidence = positive_support.copy()
        reasons: list[str] = []

        if positive_support:
            if negative_support:
                reasons.append("support evidence found with separate negative caveats")
            return JobMatch(
                job=job,
                status=MatchStatus.INCLUDED,
                matched_keywords=role_matches,
                support_evidence=evidence,
                reasons=reasons or ["visa or relocation support found"],
            )

        if remote_restrictions and not remote_eligible:
            return JobMatch(
                job=job,
                status=MatchStatus.EXCLUDED,
                matched_keywords=role_matches,
                support_evidence=negative_support + remote_restrictions,
                reasons=["remote geography excludes Bangladesh or is restricted elsewhere"],
            )

        if remote_eligible and (remote_flag or remote_markers):
            return JobMatch(
                job=job,
                status=MatchStatus.INCLUDED,
                matched_keywords=role_matches,
                support_evidence=remote_markers + remote_eligible,
                reasons=["remote eligibility includes Bangladesh, worldwide, Asia/APAC, or UTC+6"],
            )

        if negative_support and not (remote_flag or remote_markers):
            return JobMatch(
                job=job,
                status=MatchStatus.EXCLUDED,
                matched_keywords=role_matches,
                support_evidence=negative_support,
                reasons=["no visa, sponsorship, relocation, or qualifying remote support"],
            )

        if remote_flag or remote_markers:
            status = MatchStatus.REVIEW
            if self.config.strictness == "broad":
                status = MatchStatus.INCLUDED
            elif self.config.strictness == "strict":
                status = MatchStatus.EXCLUDED
            return JobMatch(
                job=job,
                status=status,
                matched_keywords=role_matches,
                support_evidence=remote_markers or ["remote flag"],
                reasons=["remote role needs manual geography verification"],
            )

        return JobMatch(
            job=job,
            status=MatchStatus.EXCLUDED,
            matched_keywords=role_matches,
            support_evidence=negative_support,
            reasons=["no visa, relocation, or eligible remote evidence"],
        )


def _labels_for_rules(rules: list[PatternRule], text: str) -> list[str]:
    labels: list[str] = []
    for rule in rules:
        if rule.pattern.search(text):
            labels.append(rule.label)
    return labels


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _remove_negated_support(positive: list[str], negative: list[str]) -> list[str]:
    negative_text = " ".join(negative).lower()
    filtered: list[str] = []
    for label in positive:
        label_text = label.lower()
        if "visa" in label_text and any(term in negative_text for term in ["visa", "sponsor"]):
            continue
        if "relocation" in label_text and "relocation" in negative_text:
            continue
        if "authorization" in label_text and "authorization" in negative_text:
            continue
        filtered.append(label)
    return filtered
