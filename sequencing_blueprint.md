
=========================================
File: c:\Users\Imart\Desktop\Multi Agent\Spec Sequencing Agent Final.json
=========================================

--- Code Node: Extract Buyer CSV URL ---
const data = $input.first().json;
const stepFiles = data?.steps?.step_11_normalizer_output?.root_files ?? [];
const normFiles = data?.normalization?.final_stats ?? [];
const updated = Array.isArray(stepFiles) ? stepFiles.find(f => f?.filename === 'updated_spec_value_counts_cumulative.csv') : null;
c...

--- Code Node: Process Buyer CSV ---
const allItems = $input.all();
if (!allItems || allItems.length === 0) return [{ json: { buyer_specs: [] } }];
const grouped = {};
for (const item of allItems) {
  const row = item.json;
  const spec = row.normalised_spec_name;
  if (!spec) continue;
  if (!grouped[spec]) grouped[spec] = { spec_name...

--- Code Node: Build Mapper Input ---
// ============================================================
// BUILD MAPPER INPUT
// All 5 sources come through Merge (append mode).
// Identify each source by structure and extract spec name lists.
// ============================================================

const allItems = $input.all().ma...

--- Node: Mapper Agent (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =You are a spec-name mapping agent for an Indian B2B marketplace.

Category: {{ $json.category_name }}

## Task
Map spec names from multiple sources to the CANONICAL spec list.

The canonical spec list is the master list of specs for this category.  
Your task is to identify which spec names from the other sources correspond to each canonical spec.

### SOURCE 1 — Seller Spec Names (MASTER LIST)
{{ JSON.stringify($json._raw_seller_specs, null, 2) }}

### SOURCE 2 — Buyer Call Spec Names
{{ JSON.stringify($json.buyer_call_spec_names, null, 2) }}

### SOURCE 3 — Fill Rate Spec Names
{{ JSON.stringify($json.fill_rate_spec_names, null, 2) }}

### SOURCE 4 — Buyer Search Spec Names
{{ JSON.stringify($json.search_spec_names, null, 2) }}

## Rules

1. For EACH canonical spec, find matching names from the other 3 sources.
2. Handle:
   - synonyms
   - abbreviations
   - word order changes
   - units (mm, inch, micron, etc.)
   - singular/plural variations
3. A source spec name can map to **at most ONE canonical spec**.
4. If no match exists for a source, return an empty array.
5. Output EXACTLY the canonical spec names provided in SOURCE 1.
6. Do NOT invent new spec names.
7. Do NOT remove any canonical spec names.
8. Do NOT include any numbers or scoring in the output.
9. Match based only on semantic meaning of the spec names.

## Output Format
STRICT JSON ONLY — no markdown, no explanations.

{
  "category_name": "<same as input>",
  "mappings": [
    {
      "seller_spec_name": "<exact name from SOURCE 1>",
      "matched_call_names": ["<buyer call name>", "..."],
      "matched_fill_rate_names": ["<fill rate name>", "..."],
      "matched_search_names": ["<search name>", "..."],
      "match_confidence": "high|medium|low"
    }
  ]
}

--- Code Node: Parse Mapper Output ---
// Parse mapper output — extract name mappings only

const first = $input.first().json;
const llmOutput = first.output ?? first.text;

if (!llmOutput || typeof llmOutput !== 'string') {
  throw new Error('No string output from Mapper Agent.');
}

// Remove markdown if model accidentally adds it
let ...

--- Code Node: Join Numbers (Code) ---
// ============================================================
// JOIN NUMBERS — Use mapper name mapping to pull actual numbers
// from raw source data. LLM never touches numbers.
// ============================================================

// ---------- Helper: normalize spec names ----------
...

--- Node: Branch A — LLM Sequencing (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =You are a Spec Sequencing Agent in a large Indian B2B marketplace.

Your job is to determine the importance order of product listing specifications for a given category, and assign each spec to a tier. 

-----------------------------------------------------
CATEGORY
-----------------------------------------------------
MCAT ID: {{ $json.mcat_id }}
Category Name: {{ $json.category_name }}

-----------------------------------------------------
SPEC DATA (one row per spec, all signals pre-joined)
-----------------------------------------------------
{{ JSON.stringify($json.unified_specs, null, 2) }}

-----------------------------------------------------
WHAT EACH SIGNAL MEANS
-----------------------------------------------------

You have 3 signals per spec. NONE of them is sufficient alone.
A spec is truly important only when MULTIPLE signals agree.

FILL RATE (Seller Signal)
  Percentage of seller product listings where this spec is filled in.
  Measures: How essential sellers consider this spec for their listings.

  Strengths:
  - Independent from buyer behavior — a direct seller-side signal of
    listing completeness.
  - Very high fill rate (>80%) means sellers universally treat this spec
    as essential to describe their product. This is not just a habit —
    it reflects what sellers know buyers need to evaluate a listing.
  - Captures specs that are critical for listing quality even when buyer
    search or call data is noisy or sparse.

  Weaknesses / Pitfalls:
  - Sellers may fill out specs out of habit or because the field is mandatory.
  - High fill rate alone doesn't guarantee buyers actively filter on it.


Bottom line: High fill rate (>80%) combined with ANY buyer signal justifies Primary.
  High fill rate alone justifies Secondary — not Tertiary.


IMPRESSION (Buyer Search Signal)
  Total search impressions across all options of this spec.
  Measures: How often buyers use this spec to FILTER products during search.

  Strengths:
  - High volume, directly tracks buyer discovery behavior.

  Weaknesses / Pitfalls:
  - A spec can have high impressions because it's a default filter on the
    platform, not because buyers actively care.
  - Implied specs (e.g., "Material" in "HDPE Tarpaulin") get inflated
    impressions from category name, not real choice.
  - A spec with ONE dominant option gives high total
    but low differentiation.

  Bottom line: High impression is a HYPOTHESIS that the spec matters.
  It needs CONFIRMATION from Product Count or Fill Rate.

PRODUCT COUNT (Buyer Call Signal)
  Number of products where this spec was discussed during actual buyer-seller calls.
  Measures: What buyers ACTUALLY talk about when making purchase decisions.

  Strengths:
  - Closest to ground truth — reflects real buyer decision-making.
  - Captures specs that are important in practice.
  - Top-discussed specs in calls are strong indicators of crucial specs.

  Weaknesses / Pitfalls:
  - Can be inflated by implied specs (buyers repeat category name words).
  - Low count doesn't always mean unimportant — some specs are assumed/obvious.

  Bottom line: High Prod Count is strong evidence of buyer importance,
  especially when confirmed by Impression or Fill Rate. Fill Rate is a CO-EQUAL signal for listing completeness.
 
EXAMPLE VALUES
  Actual option values observed in buyer call data.
  Use to check: Does this spec have real variety (multiple meaningful options)?
  Or is it single-value / noise?

MATCH CONFIDENCE
  How confidently the name-mapping agent matched this spec across sources.
  "low" = signal numbers may be unreliable for this spec.

-----------------------------------------------------
TIER DEFINITIONS
-----------------------------------------------------
PRIMARY (exactly 2-3 specs)
  The most fundamental identifiers of the product.
  A buyer CANNOT meaningfully describe or search for this product without these.
  A seller CANNOT create a complete, identifiable listing without these.

  Buyer test: What would a buyer say FIRST when asking for this product?
  Example: For "Designer Lehenga Choli" → "I need a Bridal Georgette Lehenga"
  → Type and Fabric are Primary.

  Seller test: What specs would a seller fill first to make this listing
  identifiable? What specs, if left blank, would make the listing feel
  incomplete or uncategorisable?

SECONDARY (exactly 3-4 specs)
  Specs that determine whether a specific variant works for the buyer,
  and that sellers need to distinguish one SKU from another.

  Buyer test: After specifying Primary specs, what does the buyer ask next?
  Example: "Semi-stitched, A-Line, 5 meter flair"
  → Stitching Type, Style, Flair are Secondary.

  Seller test: What specs help a seller accurately describe the specific
  variant they are listing? What specs separate one SKU from another
  within this category?

TERTIARY
  Helpful for final differentiation. Nice to know, not critical for
  identification or listing completeness.

  Test: Would a buyer still find the right product without specifying this?
  Would a seller's listing still be complete and accurate without it?
  If yes to both → Tertiary.

-----------------------------------------------------
SIGNAL CONVERGENCE FRAMEWORK (use this instead of a fixed priority)
-----------------------------------------------------

DO NOT rank specs by a single signal. Instead, evaluate CONVERGENCE:

STRONG SIGNAL (→ Primary/Secondary candidate):
  Spec is high in AT LEAST 2 of the 3 signals.
  Examples:
  - High ProdCount + High FillRate → very strong (buyers discuss, sellers fill)
  - High Impression + High FillRate → strong (search + seller listing standard)

MODERATE SIGNAL (→ Secondary/Tertiary candidate):
  Spec is high in exactly 1 signal.
  - High Impression only → maybe a default filter, not real buyer interest.
    Check example_values for variety.
  - High ProdCount only → buyers discuss it but it's not filterable.
    Could be Secondary if example_values show variety.
  - High FillRate only (>80%) → sellers treat it as a listing standard.
    Rank Secondary. Check example_values — if variety is low or spec is
    implied by category name, apply Rule 1 or Rule 2 and drop to Tertiary.

WEAK SIGNAL (→ Tertiary or drop):
  Spec is low across all 3 signals.
  Only promote if domain reasoning strongly justifies it.

CONFLICTING SIGNALS — resolution rules:
  - Impression high BUT ProdCount near zero:
    → Likely a platform default filter or implied spec. DO NOT auto-promote
      to Primary.
    → Check if the spec is IMPLIED by category name. If yes, demote.
    → If not implied, rank as Secondary at best.

  - ProdCount high BUT Impression zero:
    → Buyers care but can't filter on it. Still important.
    → Rank as Secondary. Could be Primary if ProdCount is significantly
      higher than all other specs.

  - FillRate high BUT both Impression and ProdCount low:
    → Sellers treat this as a listing standard. Rank as Secondary.
    → Only drop to Tertiary if example_values show single-value or no real
      variety, or if the spec is implied by the category name (apply Rule 1).

  - All three high:
    → Strongest Primary candidate. No conflict.

TIEBREAKER:
  When two specs have near-identical signal strength and their tier
  placement is genuinely ambiguous, use your knowledge of this product
  category and Indian B2B trade norms to break the tie.
  Flag it in change_reason as "TIEBREAKER: [reasoning]".
  Do not invoke domain knowledge to override clear signal differences.

-----------------------------------------------------
SANITY RULES (apply BEFORE finalizing tiers)
-----------------------------------------------------
You MUST check every spec against these rules and tag accordingly.

RULE 1: IMPLIED
  Trigger: The category name already fixes or strongly implies this spec's value.

  How to detect:
  - The category name contains the spec's primary value
    (e.g., "Mild Steel Bolt" → Material = Mild Steel)
  - The spec has only 1 meaningful option matching the category name
  - Example_values are all the same / all match the category-implied value
  - Impression and ProdCount are high ONLY because the implied value
    appears in every product title and every buyer query

  Action: MUST NOT be Primary or Secondary. Demote to Tertiary.
  Tag: ["IMPLIED"]

  Why: Zero differentiation. Buyers aren't choosing — they're just
  repeating the category name. High signals are an artifact, not real
  preference.

RULE 2: DATA_ARTIFACT
  Trigger: Signals look inflated or don't reflect genuine buyer choice.

  Specific cases:
  a) Brand with high ProdCount but example_values are generic
     ("Brand A", "Local", "Unbranded", "As per requirement")
  b) A spec where one option has >90% of all impressions
     (high total, but no real variety)
  c) match_confidence is "low" and numbers seem disproportionately high
  d) Spec has high impression but ZERO ProdCount — likely a default
     platform filter that buyers don't actually use actively

  Action: Tag. Do NOT auto-promote to Primary.
  Tag: ["DATA_ARTIFACT"]

RULE 3: WEAK_EVIDENCE
  Trigger: Very low signals across ALL sources.

  Thresholds:
  - Impression = 0 AND ProdCount < 5
  - OR: FillRate < 15% AND ProdCount < 3
  - OR: example_values is empty or has only 1 value

  Action: Rank in bottom half. Not in top 6 unless strong domain justification.
  Tag: ["WEAK_EVIDENCE"]


RULE 4: SINGLE_SELECT_PREFERENCE
  Prefer radio_button (single-select) for Primary tier.
  multi_select CAN be Primary if the category demands it
  (e.g., "Work" for ethnic wear where multiple work types is standard).

  Action: If promoting multi_select to Primary, justify in change_reason.


-----------------------------------------------------
OUTPUT RULES
-----------------------------------------------------

## OUTPUT RULES

- Rank ALL specs sequentially **1..N**
  - No gaps
  - No duplicates

- Maximum:
  - 3 Primary
  - 3 Secondary
  - Rest → Tertiary

- Maintain EXACT spec names from input
  - No additions
  - No removals
  - No renames

- Every spec MUST have at least one `sanity_tag`
  - Use `"OK"` if no issues found

- `change_reason` MUST cite specific numbers from ALL 3 signals

### Format

Imp: X [High/Med/Low], ProdCount: Y [High/Med/Low], FillRate: Z% [High/Med/Low].
Convergence: [STRONG/MODERATE/WEAK].
Rule applied: [OK/IMPLIED/etc….].
Tier: [Primary/Secondary/Tertiary].


- If a TIEBREAKER was applied, append:TIEBREAKER: [reasoning]

-----------------------------------------------------
OUTPUT FORMAT (STRICT JSON ONLY — no markdown, no backticks, no explanation)
-----------------------------------------------------
{
  "mcat_id": <number>,
  "category_name": "<string>",
  "method": "LLM_Reasoning",
  "results": [
    {
      "spec_name": "<exact name from input>",
      "current_tier": "<tier from input>",
      "final_rank": <integer 1..N>,
      "final_tier": "Primary|Secondary|Tertiary",
      "sanity_tags": ["OK|IMPLIED|DATA_ARTIFACT|WEAK_EVIDENCE"],
      "change_reason": "Imp: X, ProdCount: Y, FillRate: Z%. <reasoning>"
    }
  ]
}


--- Code Node: Parse Branch A ---

// ------------------------------------------------
// Parse Branch A LLM output (robust version)
// ------------------------------------------------

const first = $input.first().json;

let raw =
  first.output ??
  first.text ??
  first.message ??
  first.response ??
  null;

if (raw && typeof ra...

--- Code Node: Empty Buyer Specs ---
return [{ json: { buyer_specs: [] } }];...

--- Code Node: Get Missing Specs ---
return $input.all().map(item => {
    let fs = item.json.final_specs;
    let parsed = {};

    // 🧹 Step 1: Clean known bad patterns (defensive fix)
    if (typeof fs === 'string') {
        try {
            // Remove duplicate/broken trailing input_type entries
            fs = fs.replace(/,\s*"i...

--- Code Node: Code in JavaScript1 ---
const output = [];

for (const item of $input.all()) {
  const branch = item.json.branch;
  const mcat_id = item.json.mcat_id;
  const category_name = item.json.category_name;
  const method = item.json.method;

  const results = item.json.results || [];

  for (const spec of results) {
    output.p...

--- Code Node: Code in JavaScript3 ---
// =======================================================
// REBUILD FINAL SPEC STRUCTURE USING NEW SEQUENCE
// =======================================================

// Sequencing output rows
const rows = $input.all().map(i => i.json);

// Get original spec structure
const original = $('Get Miss...

--- Code Node: Code in JavaScript4 ---

// ============================================================
// FLATTEN unified_specs → one item per spec
// ============================================================

const item = $input.first().json;

const categoryName = item.category_name;
const mcatId = item.mcat_id;
const specs = item.u...

--- Code Node: Code in JavaScript ---
const input = $input.first().json;

const category = input.category_name;
const mappings = input.mappings || [];

const rows = [];

for (const m of mappings) {

  const sellerSpec = m.seller_spec_name;
  const confidence = m.match_confidence;

  for (const v of m.matched_call_names || []) {
    rows...
