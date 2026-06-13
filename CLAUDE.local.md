# FitFindr — Local Development Guide

## Project Overview

**FitFindr** is an AI agent for finding secondhand fashion items and generating outfit recommendations. Users describe what they're looking for, and the agent searches a mock dataset of 40 secondhand listings, then uses their wardrobe context to suggest complete outfits and generate shareable "fit cards" (Instagram/TikTok captions).

### Tech Stack
- **Python 3.10+**
- **Groq API** for LLM calls (free tier: llama-3.3-70b-versatile recommended)
- **Gradio** for web UI
- **dotenv** for environment variables

---

## Directory Structure

```
ai201-project2-fitfindr-starter/
├── agent.py                  # Planning loop orchestrator (TODO: implement run_agent)
├── app.py                    # Gradio web interface (TODO: implement handle_query)
├── tools.py                  # Three core tools (TODO: implement all)
│
├── utils/
│   └── data_loader.py        # Loads listings and wardrobe fixtures
│
├── data/
│   ├── listings.json         # 40 mock secondhand listings
│   └── wardrobe_schema.json  # Wardrobe format + example/empty templates
│
├── planning.md               # Project spec (fill out before implementation)
├── requirements.txt          # Python dependencies
├── .env                      # Local secrets (GROQ_API_KEY) — add this manually
└── CLAUDE.local.md           # This file
```

---

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Groq API Key
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up / log in (free tier)
3. Create an API key
4. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_key_here
   ```

### 3. Verify Data Loads
```bash
python utils/data_loader.py
```

Should print 40 listings and example wardrobe without errors.

---

## Core Architecture

### Data Pipeline
1. **User Query** (natural language) → **Parser** (extract description, size, max_price)
2. **search_listings()** → Top matching secondhand items
3. **suggest_outfit()** → Outfit combinations using the new item + wardrobe
4. **create_fit_card()** → Instagram-ready caption
5. **Gradio UI** displays results in three output panels

### The Three Tools

#### Tool 1: `search_listings(description, size, max_price)`
- **Purpose**: Find listings matching user's criteria
- **Input**: Keywords (e.g., "vintage graphic tee"), optional size and price filter
- **Returns**: List of matching listing dicts, sorted by relevance
- **Failure**: Returns empty list (no results) — agent must handle gracefully
- **Implementation hint**: Score listings by keyword overlap; filter by size and price

#### Tool 2: `suggest_outfit(new_item, wardrobe)`
- **Purpose**: Suggest 1–2 complete outfits combining the new item with existing wardrobe
- **Input**: Listing dict, wardrobe dict with items array
- **Returns**: String describing outfit combinations
- **Failure**: Wardrobe might be empty — offer general styling advice instead
- **Implementation hint**: Use LLM to format wardrobe items and generate outfit suggestions

#### Tool 3: `create_fit_card(outfit, new_item)`
- **Purpose**: Generate a casual, Instagram-friendly caption for the outfit
- **Input**: Outfit suggestion string, new item dict
- **Returns**: 2–4 sentence caption (casual tone, mention item name/price/platform once each)
- **Failure**: Return error message string (don't raise exception)
- **Implementation hint**: Use higher temperature to vary output; include item price and platform naturally

### Planning Loop in `agent.py`
1. Initialize session state (query, wardrobe, empty results dict)
2. Parse user query → extract `description`, `size`, `max_price`
3. Call `search_listings()` → store results in session
4. Return early if no results (set session error)
5. Select top result → store in session
6. Call `suggest_outfit()` → store outfit suggestion
7. Call `create_fit_card()` → store fit card
8. Return completed session

---

## Development Workflow

### Step 1: Fill Out `planning.md`
Complete all sections before writing code:
- [ ] Tool specs (inputs, outputs, failure modes)
- [ ] Planning loop logic
- [ ] State management approach
- [ ] Error handling table
- [ ] Architecture diagram
- [ ] Example interaction walkthrough
- [ ] AI tool plan (how you'll implement each piece)

### Step 2: Test Data Loading
```bash
python utils/data_loader.py
```

### Step 3: Implement Tools (in order)
1. **Test `search_listings()` in isolation**
   - Try: `search_listings("vintage graphic tee", size="M", max_price=30)`
   - Verify results are sorted by relevance
   - Test no-results case
   
2. **Test `suggest_outfit()` in isolation**
   - Create a test listing and wardrobe
   - Try with non-empty wardrobe
   - Try with empty wardrobe
   
3. **Test `create_fit_card()` in isolation**
   - Pass outfit suggestion + listing
   - Verify caption reads naturally
   - Check that price and platform are mentioned

### Step 4: Implement Planning Loop
Run the agent via CLI:
```bash
python agent.py
```
Should output two test cases: happy path (graphic tee) and no-results path.

### Step 5: Implement Gradio Handler
Run the web interface:
```bash
python app.py
```
Open the URL (usually `http://localhost:7860`)
- Type a query
- Select wardrobe (example or empty)
- Click "Find it"
- Verify all three output panels populate correctly

---

## Running the Application

### CLI Testing (agent only)
```bash
python agent.py
```
Outputs session results for two test queries.

### Web UI (full app)
```bash
python app.py
```
Then open `http://localhost:7860` and interact with the interface.

---

## Key Files to Review

- **[planning.md](planning.md)** — Full project spec (start here before coding)
- **[agent.py](agent.py)** — Planning loop skeleton + session management
- **[tools.py](tools.py)** — Three tools with detailed docstrings
- **[app.py](app.py)** — Gradio layout (already wired, just need handler)
- **[utils/data_loader.py](utils/data_loader.py)** — Data loading utilities
- **[data/listings.json](data/listings.json)** — 40 mock secondhand items
- **[data/wardrobe_schema.json](data/wardrobe_schema.json)** — Wardrobe format + fixtures

---

## Example User Flow

**Query**: "I'm looking for a vintage graphic tee under $30, size M"

1. **Parser**: Extract `description="vintage graphic tee"`, `size="M"`, `max_price=30`
2. **Search**: Find 3 matching listings, sorted by relevance
3. **Select**: Pick top result (e.g., "Y2K Vintage Nirvana Tee")
4. **Outfit**: LLM suggests: "Pair with your black baggy jeans and chunky white sneakers for a retro streetwear vibe"
5. **Fit Card**: LLM generates: "Found this Y2K Nirvana tee for $28 on Depop 🛍️ Giving grunge meets streetwear with my baggy denim + chunky sneakers. The faded graphic hits different 🖤✨"
6. **UI**: Display listing details, outfit suggestion, and fit card in three side-by-side panels

---

## Testing Checklist

- [ ] `python utils/data_loader.py` — no errors
- [ ] `python agent.py` — both test cases run (happy path + no-results)
- [ ] Web UI loads: `python app.py` → open localhost
- [ ] Example queries work in the UI (try the pre-filled examples first)
- [ ] Empty query returns error gracefully
- [ ] No-results query (e.g., "designer ballgown size XXS under $5") shows error in first panel
- [ ] Empty wardrobe suggestion still returns styling advice
- [ ] Fit cards read naturally (not robotic)

---

## Common Issues

**GROQ_API_KEY not set**
→ Create `.env` file with `GROQ_API_KEY=your_key`

**ImportError: No module named groq**
→ `pip install -r requirements.txt`

**No listings match**
→ This is expected for some queries. Agent should return a helpful error message, not crash.

**Gradio won't load**
→ Check that port 7860 is free, or change the port in `app.py` via `demo.launch(server_name="127.0.0.1", server_port=7861)`

---

## Next Steps (Stretch Features)

Once the core is working, consider:
- **Ranking by condition/brand** in search results
- **Multi-item outfits** (suggest 3+ pieces from wardrobe, not just 1)
- **Color palette matching** (suggest items that match new item colors)
- **User wardrobe persistence** (save wardrobe to JSON between sessions)
- **Price prediction** (suggest similar items in different price ranges)

---

## Reference

- [Groq API docs](https://console.groq.com/docs) — model options, rate limits
- [Gradio docs](https://www.gradio.app) — UI components, events
- [planning.md template](planning.md) — copy sections from here when documenting decisions