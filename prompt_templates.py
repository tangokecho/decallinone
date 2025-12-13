"""Prompt templates for artifact generation."""
from textwrap import dedent


def business_plan_prompt(title: str) -> str:
    return dedent(
        f"""
        You are creating a forward-looking 2026 business plan.
        Business Idea: {title}

        Produce a concise but complete plan with the following sections:
        1. Executive Summary
        2. Market
        3. Offer
        4. Revenue Model
        5. Marketing
        6. Operations
        7. Risks
        8. 90-Day Roadmap

        Keep it structured, markdown formatted, and action-oriented.
        """
    ).strip()


def summary_prompt(title: str) -> str:
    return dedent(
        f"""
        Summarize the following business idea in one page of plain text.
        Idea: {title}
        Highlight audience, core offer, differentiation, and near-term steps.
        """
    ).strip()


def tiktok_prompt(title: str) -> str:
    return dedent(
        f"""
        Create a short-form video script for TikTok/Reels.
        Business idea: {title}
        Include a hook, an energetic body, and a clear call to action.
        Keep it punchy and under 120 words.
        """
    ).strip()


def offer_ladder_prompt(title: str) -> str:
    return dedent(
        f"""
        Build an offer ladder for the idea "{title}".
        Include: free value asset, low-ticket paid offer, mid-ticket core offer, and a high-ticket premium option.
        Keep each item actionable and clearly priced.
        """
    ).strip()


def funnel_copy_prompt(title: str) -> str:
    return dedent(
        f"""
        Write funnel copy for a landing page promoting: {title}
        Provide hero statement, 3-5 bullet benefits, social proof idea, and a strong CTA.
        Keep tone clear, confident, and conversion-focused.
        """
    ).strip()
