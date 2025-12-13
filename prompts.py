"""Prompt templates for business plan asset generation."""

PLAN_TEMPLATE = """
You are an expert business strategist writing a 2026-ready business plan.
Business idea: {title}
Source list: {source}

Follow this structure with concise, actionable detail:
1. Executive Summary
2. Market
3. Offer
4. Revenue Model
5. Marketing
6. Operations
7. Risk
8. 90-Day Roadmap
"""

SUMMARY_TEMPLATE = """
Create a one-page plain-text summary for the business idea below. Be concise and actionable.
Idea: {title}
"""

TIKTOK_TEMPLATE = """
Write a short-form video script for TikTok/Reels promoting this business idea. Include a hook, body, and CTA.
Idea: {title}
"""

OFFER_LADDER_TEMPLATE = """
Describe a clear offer ladder (free, low-ticket, mid-ticket, high-ticket) for this idea. Use bullets and pricing guidance.
Idea: {title}
"""

FUNNEL_COPY_TEMPLATE = """
Write persuasive landing page copy: hero statement, 3-5 benefit bullets, and a strong CTA tailored to the idea.
Idea: {title}
"""
