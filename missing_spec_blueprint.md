
=========================================
File: c:\Users\Imart\Desktop\Multi Agent\Missing Spec Optimizer - Complete Flow v2.json
=========================================

--- Code Node: Seller Spec Link ---
const item = $json;

function get(obj, path, def = undefined) {
  return path.split('.').reduce((a, b) => (a && a[b] !== undefined) ? a[b] : def, obj);
}

const mcat_id = item.mcat_id || get(item, 'mcatId') || null;

let url = get(item, 'finalized_specs.file_info.url');

if (!url) {
  const fileInfo...

--- Code Node: Current Specs ---
// Extract and store seller specs for downstream use
const sellerData = $json;

const primary = sellerData.finalized_specs?.finalized_primary_specs?.specs || [];
const secondary = sellerData.finalized_specs?.finalized_secondary_specs?.specs || [];
const tertiary = sellerData.finalized_specs?.finaliz...

--- Code Node: Custom Spec Summary ---
const items = $input.all();

const output = items.map(item => {
  const data = item.json;
  const mcatId = data["Mcat Id"];
  const mcatName = data["Mcat Name"];

  let missingSpecs = [];
  try {
    missingSpecs = JSON.parse(data["Missing Spec"] || "[]");
  } catch (e) {
    missingSpecs = [];
  }
...

--- Code Node: Buyer Seller Call Summary ---
const rows = $input.all();

const specMap = {};
let mcat_name = null;

for (const item of rows) {
  const spec = item.json.spec_name;
  const values = item.json.example_values;

  if (!mcat_name && item.json.category) {
    mcat_name = item.json.category;
  }

  if (!spec) continue;

  if (!specMap[...

--- Code Node: Buyer Search Data Summary ---
const rows = $input.all();

const specMap = {};
let mcat_name = null;

for (const item of rows) {
  // Try multiple possible column names
  const spec = item.json.spec_name || item.json.search_spec || item.json.attribute;
  const values = item.json.example_values || item.json.search_values || item.j...

--- Code Node: Build Candidate Specs ---
// Combine all sources into unified candidate specs
const items = $input.all();

// Get current specs from the first pipeline
const currentSpecsNode = $items("Current Specs")[0].json;
const mcat_id = currentSpecsNode.mcat_id;
const mcat_name = currentSpecsNode.mcat_name;
const current_specs = curren...

--- Node: AI Agent 1 - Normalization (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =# ROLE

You are a **Product Specification Normalization Agent** for a large Indian B2B marketplace.

Your task is to **clean, standardize, merge, and deduplicate candidate specifications** discovered from multiple sources, producing a **canonical list of unique product attributes**.

You must also **compare candidate specs with existing seller specifications** and remove any candidates that are semantically overlapping.

IMPORTANT:  
- You **ONLY normalize candidate specifications**.  
- **Do NOT invent new specifications**.

---

# INPUT STRUCTURE

Category Name: `{{ $json.mcat_name }}`

### Candidate Specs
{{ JSON.stringify($json.candidate_specs) }}

### Seller Specs
{{ JSON.stringify($json.current_specs) }}

Each specification contains:
- `spec_name`
- `sample_values`
- `source`

---

# OBJECTIVE

Produce a **fully deduplicated and normalized list of candidate specifications** such that:

1. Formatting duplicates, spelling variations, and abbreviations are merged.
2. Singular/plural differences are unified.
3. Semantic duplicates are merged:
   - Candidate ↔ Candidate
   - Candidate ↔ Seller (candidate removed if overlapping)
4. Each final candidate represents **one unique attribute**.
5. Sample values from merged specs are combined and deduplicated.
6. Sources contributing to each spec are preserved.
7. No semantic or exact duplicates remain.

---

# NORMALIZATION RULES

## 1 Format Normalization
Treat formatting differences as identical.
Example: Weight / WEIGHT / weight → Weight

## 2 Abbreviation Expansion
Expand abbreviations to full form when possible.
Example: Qty → Quantity, No → Number

## 3 Typo Correction
Fix obvious spelling mistakes.
Example: Voltge → Voltage

## 4 Singular/Plural Normalization
Normalize to singular.
Example: Grades → Grade, Applications → Application

## 5 Semantic Similarity Merging
Merge specs representing the same attribute.
- Candidate ↔ Candidate duplicates merged
- Candidate overlapping with seller spec → remove candidate
Example:  
Size / Dimensions / Product Size → Dimensions  
Material Type / Material Grade → Material  

---

# CANONICAL SPEC NAME SELECTION

When merging multiple specs:

1. Use the most clear, concise, commonly used marketplace name.
2. Avoid abbreviations if a full form exists.
3. Prefer industry-standard terminology.
4. Ensure each spec represents **exactly one attribute**.

---

# SAMPLE VALUE HANDLING

- Combine sample values from merged specs.
- Remove duplicates.
- Preserve original value formats.
- Do not invent new values.

---

# SOURCE TRACKING

- Include **all contributing sources** in the `sources` field.
- Example: `["custom_specs","buyer_seller_call"]`

---

# FINAL VALIDATION (MANDATORY)

Before returning, ensure:

1. No duplicate or semantically overlapping candidate specs remain.
2. No candidate duplicates a seller spec.
3. Each candidate represents **exactly one attribute**.
4. Spec names follow naming rules.
5. Sample values and sources are preserved and deduplicated.

---

# NAMING RULES

- Title Case
- No ALL CAPS
- Remove trailing punctuation
- Concise and professional
- Represent **one attribute only**

---

# OUTPUT FORMAT

Return ONLY valid JSON:

{
  "mcat_name": "{{ $json.mcat_name }}",
  "normalized_candidate_specs": [
    {
      "spec_name": "Canonical Spec Name",
      "merged_from": ["Original Spec 1","Original Spec 2"],
      "sources": ["custom_specs","buyer_seller_call","buyer_search_data"],
      "sample_values": ["value1","value2"]
    }
  ]
}

Return ONLY valid JSON. No explanations.

--- Code Node: Parse Normalization Output ---
const raw = $json.output || "";

// Remove markdown wrappers
let cleaned = raw
  .replace(/```json/g, "")
  .replace(/```/g, "")
  .trim();

// Extract JSON object
const start = cleaned.indexOf("{");
const end = cleaned.lastIndexOf("}");

if (start !== -1 && end !== -1) {
  cleaned = cleaned.slice(s...

--- Node: AI Agent 3 - Option Generation (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =# ROLE
You are an **Option Generation Agent** for a large Indian B2B marketplace.
Your task is to generate **standardised, market-relevant option values** for candidate 
product specifications.

---

# INPUT TYPE CLASSIFICATION RULES

## MUST be `text_type` (options = []):
- Model numbers, SKU codes, part numbers, serial numbers
- Brand names ONLY when the category has no dominant brands 
  (default to generating options if 3+ brands are known in Indian B2B market)
- Exact custom dimensions (e.g., "Custom Size", "As per drawing")
- Free-form descriptions (e.g., "Special Features", "Additional Notes")
- Specs where no standard commercial values exist
- Specs with infinite valid variations

## MUST be `radio_button`:
- Single-choice attributes (Material Type, Power Source, Grade)
- Mutually exclusive states (Yes/No, Indoor/Outdoor)
- Single numeric ratings (Voltage, Power, Speed)
- Attributes where a product has exactly ONE value

## MUST be `multi_select`:
- Attributes where a single product can simultaneously have MULTIPLE values
- Examples: Certifications (ISO 9001 AND CE AND BIS), 
            Compatible With (multiple machine types),
            Features (Soft Start AND Overload Protection AND Variable Speed)
- When in doubt: ask "can one product have more than one value?" — if yes, multi_select

---

# OPTION GENERATION RULES

## Quality Rules:
1. **Maximum 10 options** for radio_button specs — choose the 10 MOST COMMON in 
   Indian B2B trade. For multi_select specs, up to 15 options are allowed.
2. **No duplicates** — "10 kg", "10kg", "10 Kg" are the same. Keep only one.
3. **No vague fillers** — Never use: Other, Custom, NA, Various, As Required, 
   Any, Miscellaneous, General Purpose (unless it is a genuinely traded category value)
4. **Under 30 characters** per option
5. **Standardised units** — Always use: kg, mm, V, W, A, rpm, °C, %, L, mL, Hz
   Never use: kgs, MM, Volt, Watts, Amps, Celsius

## Formatting Rules:
6. **Compact numeric format** — "12V" not "12 Volt"; "50Hz" not "50 cycles per second"
7. **Title Case for text** — "Stainless Steel" not "stainless steel" or "STAINLESS STEEL"
8. **Popularity order** for numeric options — 5mm, 10mm, 15mm, 20mm. Ensure to include the most popular options first..
9. **Frequency-based order** for categorical options — most common in Indian market first

10. Use ISI/BIS standards where applicable.
11. Use local trade terminology — "GI" for Galvanized Iron, "MS" for Mild Steel
12. Do not give range type options until market standard for the spec
12. Think like a Indian B2B seller — what spec values would a seller actually use?

---

# HANDLING SAMPLE VALUES

Sample values are hints about FORMAT and MEANING only — not the final options list.

| Sample Quality | Action |
|---|---|
| Clean, consistent values | Use as format reference; generate full standard market set |
| Mixed quality (some good, some bad) | Extract the pattern; discard outliers |
| Thin (1–2 values only) | Use to confirm spec meaning; generate full options from market knowledge |
| Completely messy or random | Ignore entirely; generate from category + spec name knowledge |
| Empty | Generate entirely from category + spec name knowledge |
| Contains "NA", "Other", "Custom" | Ignore these values; treat as empty |

---

# EDGE CASE HANDLING

## Ambiguous spec names:
Interpret in context of the specific category. "Size" means different things for 
Bearings vs Apparel vs Pipes. Choose the commercially meaningful interpretation.

## Spec seems irrelevant to category:
Still generate options if standard values exist. Do not skip or drop specs.

## Yes/No specs:
Options: ["Yes", "No"] with input_type: "radio_button"


---

# TIER ASSIGNMENT RULES : For candidate specs (newly discovered), default to Tertiary as given in the input. 


---

# VALIDATION CHECKLIST

Before finalizing each spec, verify:
- [ ] Options are directly about THIS spec, not adjacent attributes
- [ ] Options make sense for this specific category
- [ ] A real buyer would use these as search filters
- [ ] No duplicates or near-duplicates
- [ ] No vague or filler options
- [ ] Correct input_type for the spec's nature
- [ ] Logical order (ascending numeric or frequency-based categorical)
- [ ] All options under 30 characters
- [ ] Units are standardized

---

# INPUT

**Category:** {{ $json.mcat_name }}

**Candidate Specs:**
{{ JSON.stringify($json.candidate_specs) }}

---

# OUTPUT FORMAT

Return ONLY raw valid JSON. No markdown fences, no explanations, no preamble.
The response must start with { and end with }

{
  "mcat_name": "Category Name",
  "finalized_specs_with_options": [
    {
      "spec_name": "Spec Name",
      "options": ["Option1", "Option2", "Option3"],
      "input_type": "radio_button",
      "tier": "Tertiary",
      "sources": ["custom_specs", "buyer_seller_call"]
    },
    {
      "spec_name": "Free Form Spec",
      "options": [],
      "input_type": "text_type",
      "tier": "Tertiary",
      "sources": ["custom_specs"]
    }
  ]
}

---

# COMMON MISTAKES TO AVOID

1. Wrapping output in ```json fences — output must start with { directly
2. Generating options for a different attribute than the spec name
3.. Adding any text, explanation, or commentary outside the JSON



--- Code Node: Parse Agent 3 Output ---
let raw = $json.output || "";

raw = raw.replace(/```json/g, "").replace(/```/g, "").trim();

const start = raw.indexOf("{");
const end = raw.lastIndexOf("}");

if (start !== -1 && end !== -1) {
  raw = raw.substring(start, end + 1);
}

raw = raw
  .replace(/,\s*]/g, "]")
  .replace(/,\s*}/g, "}");
...

--- Code Node: Combine Specs with Options ---
const sellerNode = $items("Current Specs")[0].json;
const optionNode = $items("Parse Agent 3 Output")[0].json;

const mcat_id = sellerNode.mcat_id;
const mcat_name = sellerNode.mcat_name;

const sellerSpecs = sellerNode.current_specs || [];
const candidates = optionNode.finalized_specs_with_options ...

--- Code Node: Format Final Output ---
const data = $json;

const mcatId = data.mcat_id;
const mcatName = data.mcat_name;
const specs = data.finalized_specs || [];

const primary = [];
const secondary = [];
const tertiary = [];

specs.forEach(spec => {
  const specObj = {
    spec_name: spec.spec_name,
    options: spec.options || [],
  ...

--- Code Node: Code in JavaScript1 ---
const data = $json;

const mcat_name = data.mcat_name;
const normalized = data.normalized_candidate_specs || [];

const candidate_specs = normalized.map(spec => ({
  spec_name: spec.spec_name,
  sample_values: spec.sample_values || [],
  sources: spec.sources || []
}));

return [
  {
    json: {
   ...

--- Node: AI Agent 1 - Normalization1 (@n8n/n8n-nodes-langchain.agent) ---
TEXT: # ROLE
You are a **Product Specification Normalization and Merging Agent** for a large Indian B2B marketplace.

Your task is to:
1. Clean, standardize, and deduplicate candidate specifications from multiple sources
2. Remove candidates that semantically overlap with existing seller specs
3. Append the final validated candidates to the existing specs list
4. Return the complete, final specification set ready for use

IMPORTANT:
- You **ONLY normalize and filter candidate specifications**
- You **DO NOT invent new specifications**
- You **DO NOT modify existing seller specs** in any way
- Existing seller specs are always preserved exactly as-is

---

# INPUT STRUCTURE

Category Name: `{{ $json.mcat_name }}`

### Existing Seller Specs (DO NOT MODIFY)
{{ JSON.stringify($json.current_specs) }}

### Candidate Specs to Normalize (from multiple sources)
{{ JSON.stringify($json.candidate_specs) }}

Each candidate spec contains:
- `spec_name` — the attribute name
- `sample_values` — example values for this attribute
- `source` — origin of this spec (e.g., custom_specs, buyer_seller_call, buyer_search_data)

---

# STEP 1 — NORMALIZE CANDIDATE SPECS

Apply all normalization rules to each candidate spec:

## Rule 1: Format Normalization
Treat all formatting differences as identical. Normalize to Title Case.
Example: WEIGHT / weight / Weight → Weight

## Rule 2: Abbreviation Expansion
Expand common abbreviations to full form.
Examples: Qty → Quantity, No → Number, Pkg → Packaging, Mfr → Manufacturer, Min → Minimum, Max → Maximum

## Rule 3: Typo Correction
Fix obvious spelling mistakes.
Example: Voltge → Voltage, Dimesnion → Dimension

## Rule 4: Singular/Plural Normalization
Always normalize to singular form.
Examples: Grades → Grade, Applications → Application, Colors → Color, Types → Type

## Rule 5: Candidate ↔ Candidate Semantic Merging
Identify candidate specs that represent the same underlying attribute and merge them into one.
- Choose the most professional, marketplace-appropriate canonical name
- Combine all sample_values and deduplicate
- Combine all sources and deduplicate
- Track all original names in merged_from

Examples:
- Size / Dimensions / Product Size → Size
- Material Type / Material Grade / Material Quality → Material
- Pack Quantity / Packaging Quantity / Pack Size → Packaging Quantity
- Color / Colour / Product Color → Color

---

# STEP 2 — FILTER AGAINST EXISTING SELLER SPECS

After normalizing candidates among themselves, compare every remaining candidate against the existing seller specs.

**Remove a candidate if:**
- It is an exact name match (case-insensitive) with any existing spec
- It is a semantic duplicate of an existing spec (same attribute, different wording)

**Semantic overlap examples to remove:**
- Candidate "Product Color" → remove (seller already has "Color")
- Candidate "Material Type" → remove (seller already has "Material")
- Candidate "Usage Occasion" → remove (seller already has "Occasion")
- Candidate "Bangle Type" → remove (seller already has "Type")
- Candidate "Pack Quantity" → remove (seller already has "Set Content")

**Keep a candidate if:**
- It represents a genuinely new attribute not covered by any existing spec
- There is no semantic overlap with any existing spec

When in doubt about whether overlap exists, err on the side of removing the candidate.

---

# STEP 3 — FINAL CANDIDATE VALIDATION

Before proceeding, verify each surviving candidate:
1. Spec name follows Title Case, no abbreviations, no trailing punctuation
2. Spec name represents exactly ONE attribute
3. No two surviving candidates represent the same attribute
4. No surviving candidate overlaps with any existing seller spec
5. Sample values are deduplicated and preserve original formats
6. Sources list is deduplicated

---

# STEP 4 — CONSTRUCT FINAL MERGED SPEC LIST

Build the output by:
1. Taking ALL existing seller specs exactly as provided (preserve spec_name, options, input_type, tier)
2. Appending surviving normalized candidates at the end with the following structure:
   - `spec_name`: canonical name
   - `options`: use sample_values array (renamed to options for consistency)
   - `input_type`: always set to "radio_button" for new candidates
   - `tier`: always set to "Tertiary" for new candidates
   - `sources`: list of contributing sources (extra metadata field)
   - `merged_from`: list of original spec names before normalization (extra metadata field)

---

# NAMING RULES (apply to all candidate spec names)
- Title Case only
- No ALL CAPS
- No abbreviations if full form exists
- No trailing punctuation
- Concise and professional
- Represents exactly one attribute

---

# OUTPUT FORMAT

Return ONLY valid JSON in this exact structure. No explanation, no markdown, no commentary.

{
  "mcat_id": {{ $json.mcat_id }},
  "mcat_name": "{{ $json.mcat_name }}",
  "summary": {
    "existing_specs_count": <number of original seller specs, unchanged>,
    "candidates_evaluated": <total candidate specs received>,
    "candidates_removed_overlap": <count removed due to seller spec overlap>,
    "candidates_added": <count of new specs appended>,
    "final_specs_count": <total specs in final list>
  },
  "final_specs": [
    {
      "spec_name": "Spec Name",
      "options": ["value1", "value2"],
      "input_type": "radio_button",
      "tier": "Primary"
    }
  ],
  "normalized_candidates_added": [
    {
      "spec_name": "Canonical Spec Name",
      "merged_from": ["Original Name 1", "Original Name 2"],
      "sources": ["custom_specs", "buyer_seller_call"],
      "sample_values": ["value1", "value2"]
    }
  ],
  "removed_candidates": [
    {
      "spec_name": "Removed Candidate Name",
      "reason": "Semantic overlap with existing spec: <existing spec name>"
    }
  ]
}

The `final_specs` array must contain ALL existing seller specs first (in original order, unmodified), followed by the newly added candidate specs.

Return ONLY valid JSON.

--- Code Node: Code in JavaScript ---
const raw = $json.output;

// Strip markdown code fences if present
const cleaned = raw
  .replace(/^```json\s*/i, '')
  .replace(/^```\s*/i, '')
  .replace(/```\s*$/i, '')
  .trim();

const parsed = JSON.parse(cleaned);

return [{ json: parsed }];...

--- Code Node: Code in JavaScript2 ---
const data = $json;

const candidateSpecs = data.normalized_candidates_added.map(spec => ({
  spec_name: spec.spec_name,
  sample_values: spec.sample_values || [],
  sources: spec.sources || []
}));

return [
  {
    json: {
      mcat_id: data.mcat_id,
      mcat_name: data.mcat_name,
      candida...
