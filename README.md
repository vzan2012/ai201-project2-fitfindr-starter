# FitFindr — Find Secondhand Fashion, Get Outfit Ideas

You describe what secondhand piece you want. FitFindr searches for it in a database of 40 listings. It finds the best match, suggests how to style it with your wardrobe, and writes a casual Instagram caption for you. If nothing matches your search, it tells you why and what to try instead. The agent does all this in steps - search first, then outfit suggestions, then caption.

---

## How It Works: The Planning Loop

The agent isn't just executing a fixed script. It makes decisions based on what happens at each step.

**Here's the flow:**

1. **Parse the query** - You type something like `"vintage graphic tee under $30, size M"`. The agent uses regex to extract three pieces of info: what you're looking for (description), your size, and your max price. Some of these might be missing - that's okay.

2. **Search for listings** - The agent searches a dataset of 40 mock secondhand items, filters by size (case-insensitive substring match) and price, then scores each result by how many keywords from your description match the item's title, description, and style tags. Results come back sorted best-first, or an empty list if nothing matches.

3. **Decide: Did we find anything?** - This is the conditional logic moment. If the search returned zero results, the agent **stops here** and tells you why (maybe your size range is too narrow, or your budget is too tight). It doesn't proceed to the next steps. This prevents wasting API calls and gives you helpful feedback immediately.

4. **If we found results:** Pick the top item and call the second tool. The agent sends that item to `suggest_outfit()` along with your wardrobe (or an empty wardrobe if you're a new user). The LLM then suggests how to style the piece - either with specific items from your wardrobe, or with general styling advice if you don't have anything entered yet.

5. **Generate a caption** - The outfit suggestion gets passed to `create_fit_card()`, which asks the LLM to write a casual Instagram/TikTok caption. The caption naturally mentions the item name, price, and platform (Depop, Poshmark, thredUp), then talks about the styling in a way that sounds authentic, not like a product description.

6. **Return everything** - The agent gives you the item details, the outfit idea, and the caption all at once. You see all three in the Gradio interface.

**The key decision point:** If search returns nothing, the agent bails out early. You never see a null reference error or an ugly LLM response about an empty item - you get a helpful message instead.

---

## Tool Inventory

### Tool 1: `search_listings(description, size, max_price)`

**Inputs:**
- `description` (str): Keywords describing what you're looking for (e.g., `"vintage graphic tee"`)
- `size` (str | None): Size string to filter by, case-insensitive (e.g., `"M"` matches `"S/M"`). Pass `None` to skip size filtering.
- `max_price` (float | None): Maximum price (inclusive). Pass `None` to skip price filtering.

**Output:**
- `list[dict]`: A list of matching listing dicts, sorted by relevance (best matches first). Returns an empty list if nothing matches - does NOT raise an exception.

**What it does:**
Loads 40 mock secondhand listings from JSON, filters by size and price, scores each by keyword overlap, and returns the sorted results. Each listing dict contains: id, title, description, category, style_tags, size, condition, price, colors, brand, platform.

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`

**Inputs:**
- `new_item` (dict): A listing dict from `search_listings()` (contains title, description, price, colors, style_tags, etc.)
- `wardrobe` (dict): A wardrobe dict with an `"items"` key containing a list of wardrobe pieces. May be empty.

**Output:**
- `str`: A 2–3 sentence outfit suggestion.

**What it does:**
Sends the item and wardrobe to the Groq LLM (llama-3.3-70b-versatile). If the wardrobe is empty, it returns general styling advice ("This piece pairs well with..."). If the wardrobe has items, it returns specific combinations using actual piece names from the wardrobe. Always returns a non-empty string - never crashes or returns null.

---

### Tool 3: `create_fit_card(outfit, new_item)`

**Inputs:**
- `outfit` (str): The outfit suggestion string from `suggest_outfit()`
- `new_item` (dict): The listing dict

**Output:**
- `str`: A 2–4 sentence Instagram/TikTok caption

**What it does:**
Sends the outfit and item to the Groq LLM with a prompt asking for a casual, authentic-sounding caption. The caption mentions the item name, price, and platform naturally, and captures the outfit vibe. Uses temperature=0.8 so captions vary each time. Guards against empty outfit input by returning a descriptive error message instead of crashing.

---

## State Management

State flows through the agent as a single dictionary that gets built up step by step:

```python
session = {
    "query": "vintage graphic tee under $30, size M",           # original input
    "parsed": {                                                  # extracted from query
        "description": "vintage graphic tee",
        "size": "M",
        "max_price": 30.0
    },
    "search_results": [...],          # list of matching listings from search_listings()
    "selected_item": {...},           # the top result, passed to suggest_outfit()
    "wardrobe": {...},                # user's wardrobe dict
    "outfit_suggestion": "Pair with...", # output from suggest_outfit()
    "fit_card": "Just scored...",     # output from create_fit_card()
    "error": None                     # set to error message if something failed
}
```

Each tool receives what it needs from the session and adds its output back to it. The Gradio handler then formats those outputs for the three UI panels. If `error` is set, the handler returns the error in the first panel and empty strings in the other two.

---

## Error Handling

Each tool handles failures gracefully instead of crashing. Here's how:

### `search_listings()` - Empty Results
**What can go wrong:** User searches for something that doesn't exist in the dataset.

**How it handles it:** Returns an empty list `[]` instead of raising an exception.

**Example from testing:** Query `"designer ballgown size XXS under $5"` returned `[]`. The agent then checked the length and returned an early error message instead of trying to call `suggest_outfit()` on a null item.

---

### `suggest_outfit()` - Empty Wardrobe
**What can go wrong:** User has no wardrobe entered (new user).

**How it handles it:** Detects empty `wardrobe["items"]` and asks the LLM for general styling advice instead of crashing.

**Example from testing:** Called with an empty wardrobe, it returned `"This vintage forest green polo shirt is a versatile piece that can be dressed up or down..."` - useful general advice, not an error.

---

### `create_fit_card()` - Empty Outfit String
**What can go wrong:** Someone passes an empty or whitespace-only outfit string.

**How it handles it:** Guards against empty input and returns a descriptive error message.

**Example from testing:** Passing `""` as the outfit returned `"Unable to generate a fit card - outfit suggestion was incomplete."` instead of sending garbage to the LLM.

---

### Planning Loop - No Results Path
**What can go wrong:** `search_listings()` returns an empty list.

**How it handles it:** The agent checks the length and returns early with a helpful message: `"Sorry, no listings matched your search. Try different keywords, a larger size range, or a higher budget."`

**Example from testing:** Query `"designer ballgown size XXS under $5"` hit this path. The agent set `session["error"]` and returned immediately, without calling `suggest_outfit()` or `create_fit_card()`. The Gradio handler then displayed the error in the listing panel and left the other two empty.

---

### Gradio Handler - Empty Input
**What can go wrong:** User clicks "Find it" without typing anything.

**How it handles it:** Guards against empty or whitespace-only queries and returns an error message immediately: `"Please enter what you're looking for..."`

---

## Spec Reflection

### What the Spec Helped With

The `planning.md` document laid out the 8-step planning loop before I wrote any code. This was huge because it made the conditional logic explicit. Instead of writing `run_agent()` and discovering halfway through that I needed to check for empty results, I had already thought through what happens if search fails. The error handling table in the spec meant I didn't miss any edge cases.

The architecture diagram (Mermaid) also helped - it showed the data flow between tools and made it obvious that `suggest_outfit()` depends on `search_listings()` working first. I could visualize exactly what breaks if one tool fails.

### Where Implementation Diverged (and Why)

**Query parsing:** The spec said "use regex, string splitting, or ask the LLM to parse it." I went with regex because it's deterministic and fast. The LLM would've worked but would've added latency and cost for something simple (extracting a price and a size). The regex approach is also testable without needing an API key.

**Wardrobe fixtures:** The spec assumed a real database of wardrobe items. Instead, we load a hardcoded `"example_wardrobe"` dict. This is because the focus was on the planning loop logic, not persistence. In a real product, you'd hit a database here. For testing the agent's conditional logic, a JSON fixture was enough.

**Temperature tuning:** The spec didn't specify temperature values for the LLM calls. I set `create_fit_card()` to temperature=0.8 (higher variety) because captions should sound different each time. `suggest_outfit()` uses the default (0.7) because consistency in outfit advice is more important. This was a judgment call during implementation.

---

## AI Usage: What I Directed Claude To Do

### Instance 1: Planning Loop Architecture

**What I gave Claude:** The course requirements (3 tools, planning loop, state management, error handling) and asked it to design the planning loop logic in detail.

**What Claude produced:** The 8-step flow in `planning.md` with:
- Conditional logic for the "no results" path
- Session dict structure with all fields pre-defined
- Error handling table for each tool
- State flow diagram showing how data passes between tools

**What I kept:** The overall structure, the session dict design, and the conditional logic. They were solid.

**What I changed:** Claude initially suggested handling all three tools even if search failed, with empty fallbacks. I overrode this because it was wasteful - if there's no item, don't call the LLM. The early return made more sense. I updated the spec to reflect this.

---

### Instance 2: Query Parsing Implementation

**What I gave Claude:** The parsing requirements (extract description, size, max_price from natural language) and asked which approach to use.

**What Claude produced:** Suggested three options: regex, string splitting, or LLM-based parsing. Recommended LLM for flexibility but acknowledged the cost/latency tradeoff.

**What I kept:** The regex approach, which Claude had mentioned as an option. It's fast and testable.

**What I changed:** Claude initially had the regex patterns match anywhere in the query. I tightened them to look for specific patterns like `"$X"` and `"size X"` so queries like `"I'm a size M"` don't accidentally match (the size should be in the context of the search, not about the user). Also made size matching case-insensitive because users might type `"SIZE m"` or `"size S/M"`.

---

## Testing & Verification

All three tools were tested individually before wiring them into the agent:
- `search_listings()`: 6 tests (empty results, filtering, relevance sorting, no filters)
- `suggest_outfit()`: 3 tests (empty wardrobe, full wardrobe, always returns string)
- `create_fit_card()`: 5 tests (caption generation, price/platform mentions, empty outfit handling)
- Planning loop: 5 integration tests (no-results path, query parsing, session state flow)
- Gradio handler: 9 UI tests (empty input, wardrobe selection, error handling, output formatting)

**Total: 34 tests, all passing.**

---

## Running the App

### Start the Gradio Interface
```bash
python app.py
```

Open the URL shown in your terminal (usually `http://localhost:7860`).

### Test Queries
Try these to see the different paths:

**Happy path (full flow):**
```
"vintage graphic tee under $30, size M"
```
All three panels populate.

**Empty wardrobe:**
Select "Empty wardrobe (new user)" and search for anything. Middle panel gives general advice instead of specific combinations.

**Failure path (no results):**
```
"designer ballgown size XXS under $5"
```
Left panel shows error, other two are empty.

---

## Tech Stack

- **Python 3.10+** - Core language
- **Groq API** - LLM calls (llama-3.3-70b-versatile, free tier)
- **Gradio** - Web UI framework
- **pytest** - Test framework
- **python-dotenv** - Environment variable management

---

## Project Structure

```
ai201-project2-fitfindr-starter/
├── tools.py              # Three core tools (search, suggest, caption)
├── agent.py              # Planning loop (run_agent function)
├── app.py                # Gradio interface (handle_query function)
├── planning.md           # Detailed specs and architecture
├── README.md             # This file
├── requirements.txt      # Dependencies
├── .env                  # Local secrets (GROQ_API_KEY)
│
├── tests/
│   └── test_tools.py     # 34 tests (15 tool tests + 14 integration + 5 failure modes)
│
├── utils/
│   └── data_loader.py    # Loads listings.json and wardrobe fixtures
│
└── data/
    ├── listings.json     # 40 mock secondhand listings
    └── wardrobe_schema.json # Wardrobe format + example data
```

---

## Future Ideas

- **Smart ranking:** Sort results by condition, brand, or user ratings
- **Multi-item outfits:** Suggest 3+ coordinating pieces instead of just 1
- **Color matching:** Filter suggestions by color palette
- **Wardrobe persistence:** Save user's wardrobe between sessions (backend DB)
- **Improved UI:** Add filters, favorites, direct links to platforms

---

## Acknowledgments

Built for CodePath AI 201 Project 2. Uses Groq's free LLM API and Gradio's web framework.
