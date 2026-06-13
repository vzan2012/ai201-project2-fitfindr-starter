"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    # Filter by price and size
    candidates = []
    for listing in listings:
        # Skip if price is too high
        if max_price is not None and listing["price"] > max_price:
            continue

        # Skip if size doesn't match (case-insensitive substring match)
        if size is not None:
            listing_size = listing["size"].lower()
            search_size = size.lower()
            if search_size not in listing_size:
                continue

        candidates.append(listing)

    # Score each candidate by keyword overlap
    keywords = description.lower().split()
    scored = []

    for listing in candidates:
        score = 0
        searchable_text = (
            listing["title"].lower() + " " +
            listing["description"].lower() + " " +
            " ".join(listing["style_tags"]).lower()
        )

        for keyword in keywords:
            if keyword in searchable_text:
                score += 1

        # Keep items with at least one keyword match
        if score > 0:
            scored.append((score, listing))

    # Sort by score (highest first) and return
    scored.sort(key=lambda x: x[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    item_description = f"""
Item: {new_item['title']}
Description: {new_item['description']}
Style: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}
Price: ${new_item['price']}
"""

    if not wardrobe["items"]:
        # Empty wardrobe — give general styling advice
        prompt = f"""You're a casual fashion stylist. Someone just found this secondhand item and wants outfit ideas. They don't have any wardrobe entered yet, so give them general styling advice about what would pair well with this piece.

{item_description}

Give 2-3 sentences of practical, casual advice about what kinds of pieces would work with this item, what vibe it suits, and how to style it."""
    else:
        # Format wardrobe items for the prompt
        wardrobe_text = "User's wardrobe:\n"
        for item in wardrobe["items"]:
            wardrobe_text += f"- {item['name']} ({', '.join(item['style_tags'])})\n"

        prompt = f"""You're a fashion buddy helping someone style a thrifted find. They found this item and want to know how to wear it with what they already own.

{item_description}

{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and pieces from their wardrobe. Be casual and specific — mention actual wardrobe pieces by name. Keep it to 2-3 sentences."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against empty outfit
    if not outfit or not outfit.strip():
        return "Unable to generate a fit card — outfit suggestion was incomplete."

    client = _get_groq_client()

    prompt = f"""You're helping someone write a casual Instagram/TikTok caption for a secondhand find. Write a 2-3 sentence caption that sounds authentic — like a real person posting an outfit, not a product description.

Item found: {new_item['title']}
Price: ${new_item['price']}
Platform: {new_item['platform']}
Item description: {new_item['description']}

How they're styling it:
{outfit}

Write a casual, authentic caption. Include the item name, price, and platform naturally in the text. Make it sound like someone excited about a thrift haul, not a sales pitch."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.8  # Higher temperature for variety in captions
    )

    return response.choices[0].message.content
