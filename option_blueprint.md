
=========================================
File: c:\Users\Imart\Desktop\Multi Agent\Option Audit Agent v1.json
=========================================

--- Code Node: Parse Specs ---
const row = $input.first().json;

const parsedSpecs = JSON.parse(row.specs);

return [{
  json: {
    mcat_id: row.mcat_id,
    mcat_name: row.mcat_name,
    finalized_specs: parsedSpecs.finalized_specs
  }
}];...

--- Code Node: Extract Buyer CSV URL ---
const data = $input.first().json;
const stepFiles = data?.steps?.step_11_normalizer_output?.root_files ?? [];
const normFiles = data?.normalization?.final_stats ?? [];
const updated = Array.isArray(stepFiles) ? stepFiles.find(f => f?.filename === 'updated_spec_value_counts_cumulative.csv') : null;
c...

--- Code Node: Process Buyer CSV (Options) ---
// Process buyer CSV — keep OPTION-LEVEL data (don't aggregate to spec level)
// Each row: spec_name + option_value + prod_count
const allItems = $input.all();
if (!allItems || allItems.length === 0) return [{ json: { buyer_call_options: [] } }];

const options = [];
for (const item of allItems) {
 ...

--- Code Node: Empty Buyer Options ---
return [{ json: { buyer_call_options: [] } }];...

--- Code Node: Build Mapper Input ---
// ============================================================
// BUILD MAPPER INPUT — Collect all option name lists per spec
// Pass raw data through for Join Numbers
// ============================================================

const allItems = $input.all().map(i => i.json);

// ==============...

--- Node: Option Mapper Agent (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =You are an **Option Mapping Agent** for an Indian B2B marketplace.

Your ONLY task is to **map option names from multiple data sources to the canonical option list for each spec**.

You **must NOT**:

* modify canonical spec names
* modify canonical option names
* assign counts or scores
* make keep/reject decisions

Your role is **mapping only**.

---

# CATEGORY

Category: {{ $json.category_name }}
MCAT ID: {{ $json.mcat_id }}

---

# CANONICAL SPEC OPTIONS (MASTER LIST)

These are the **approved specs and options**.
They are the **single source of truth**.

DO NOT modify these names.

{{ JSON.stringify($json.current_spec_options, null, 2) }}

---

# SOURCE DATA

Source options come from multiple noisy datasets.

### SOURCE 1 — Buyer Call Options

(spec_name → option_values)

{{ JSON.stringify($json.call_option_names, null, 2) }}

---

### SOURCE 2 — Seller Fill Rate Options

(spec_name → option_values)

{{ JSON.stringify($json.fill_option_names, null, 2) }}

---

### SOURCE 3 — Buyer Search Options

(spec_name → option_values)

{{ JSON.stringify($json.search_option_names, null, 2) }}

---

# STEP 1 — MAP SOURCE SPECS TO CANONICAL SPECS

Source datasets may use **different spec names**.

First map source spec names to canonical spec names.

Match using:

### 1. Case normalization

Examples:

* "brand" → "Brand"
* "color" → "Color"

### 2. Spelling variations

Examples:

* "Colour" → "Color"
* "Material quality" → "Material Grade"

### 3. Minor wording variations

Examples:

* "Feature" → "Features"
* "Brand Name" → "Brand"

If a source spec **cannot reasonably map to any canonical spec**, ignore it.

---

# STEP 2 — MAP SOURCE OPTIONS TO CANONICAL OPTIONS

For each canonical spec, map source option values.

Use the following rules **in order**.

---

## Rule 1 — Exact Match

Case insensitive.

Example pattern:

* "Blue" ↔ "blue"
* "HDPE" ↔ "hdpe"

---

## Rule 2 — Formatting Variation

Values that represent **the same thing with different formatting** should match.

Typical variations include:

* spacing differences
* punctuation differences
* capitalization differences
* unit formatting differences
* minor spelling mistakes

Examples:

* "120GSM" ↔ "120 GSM"
* "12x18 ft" ↔ "12 x 18 ft"
* "Semi Virgin" ↔ "Semi-Virgin"
* "Aluminium" ↔ "Aluminum"

---

## Rule 3 — Numeric Unit Variations

Values that represent the **same number with or without units** may match.

Example patterns:

* number vs number + unit
* number formatting differences

Example:

* "120" ↔ "120 GSM" (if the spec clearly expects that unit)

Only apply when the **spec context clearly implies the unit**.

---

## Rule 4 — Cross-Spec Misplacement

Sometimes an option appears under the **wrong spec**.

If the value clearly belongs to a **different spec**, ignore it.

Example patterns:

* material value under color
* numeric value under brand
* feature value under size

Do not map these.

---

## Rule 5 — Multi-Value / Range Options

Options representing **multiple values or ranges** are NOT valid single options.

Examples:

* ranges: "10-20", "100 to 200"
* multiple values: "Red, Blue"
* lists: "A/B/C"

Mark these as **junk**.

---

## Rule 6 — Non-Option Text (Junk)

Ignore values that are **not actual selectable options**, such as:

### Placeholders

Examples:

* "as per requirement"
* "customized"
* "available"
* "to be confirmed"

### All/Any placeholders

Examples:

* "All"
* "Any"
* "All sizes"
* "All colours"

### Descriptions instead of options

Examples:

* product descriptions
* marketing phrases
* long sentences

### Corrupted / unreadable text

Examples:

* encoding errors
* garbled characters

### Vague labels

Examples:

* "standard"
* "normal"
* "good"
* "other"

All of these should be marked as **junk options**.

---

# STEP 3 — IDENTIFY NEW VALID OPTIONS

If a source option:

✓ does NOT match any canonical option
✓ is NOT junk
✓ represents a single clear value
✓ belongs to the correct spec

Then it is a **new option**.

Standardize the option name:

* clean capitalization
* normalize spacing
* include units if clearly implied
* remove unnecessary characters

---

# OUTPUT RULES

* Include **ALL canonical specs**, even if no matches exist.
* Do NOT modify canonical option names.
* Each canonical option must list matched source options.
* Lists may be empty `[]`.
* New options must be standardized.
* Junk options must include a reason.
* Do NOT include counts or metrics.

---

# OUTPUT FORMAT

STRICT JSON ONLY
No markdown
No commentary

```json
{
  "category_name": "<same as input>",
  "spec_option_mappings": [
    {
      "spec_name": "<exact canonical spec name>",
      "option_mappings": [
        {
          "current_option": "<exact canonical option name>",
          "matched_call_options": [],
          "matched_fill_options": [],
          "matched_search_options": []
        }
      ],
      "new_options": [
        {
          "option_value": "<standardized option>",
          "raw_source_values": [],
          "seen_in": []
        }
      ],
      "junk_options": [
        {
          "value": "<junk value>",
          "source": "call|fill|search",
          "reason": "placeholder|range|corrupted|nonsense|description|vague|wrong_spec"
        }
      ]
    }
  ]
}


--- Code Node: Parse Mapper Output ---
// Parse mapper output — option name mappings
const first = $input.first().json;
const llmOutput = first.output ?? first.text;
if (!llmOutput || typeof llmOutput !== 'string') throw new Error('No output from Option Mapper.');
let clean = llmOutput.replace(/```json\s*/gi, '').replace(/```\s*/g, '').t...

--- Node: Option Audit Agent (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =

You are an **Option Audit Agent** for an Indian B2B marketplace.

Your job is to evaluate **existing catalog options for each spec** and decide whether to:

* **KEEP** – option remains in catalog
* **REJECT** – option should be removed
* **MERGE** – option is a duplicate of another option

You must also detect **absurd or invalid options**, especially those that are **incorrect for the category–spec pair**.

Your decisions must be **consistent, deterministic, and based on the provided signals**.

---

# CATEGORY

MCAT ID: {{ $json.mcat_id }}
Category Name: {{ $json.category_name }}

---

# CURRENT OPTIONS (existing catalog options)

{{ JSON.stringify($json.current_specs, null, 2) }}

---

# SIGNAL DEFINITIONS

Each option contains signals from three independent sources.

**prod_count**
Number of products where this option appeared in buyer–seller call data.

**fill_rate**
Percentage of seller listings using this option.

**impression**
Search impressions where this option appears in buyer queries.

These represent **real marketplace signals**.

---

# STEP 1 — DETERMINE SIGNAL PRESENCE

Convert each metric into a binary signal.

Call signal:

```
prod_count > 0
```

Seller signal:

```
fill_rate > 0
```

Search signal:

```
impression > 0
```

Then compute:

```
signal_sources = number of signals present
```

Possible values: **0, 1, 2, or 3**

---

# STEP 2 — DECISION PRIORITY

Apply rules **in the following order**.

---

# RULE 1 — ABSURD OPTIONS (HIGHEST PRIORITY)

Reject immediately if the option is **absurd for the category–spec pair**, even if signals exist.

Examples:

Type mismatch

* Color spec with numeric values
* Size spec with color values
* Brand spec with numeric values

Example patterns:

Color spec:

```
25 mm
120 GSM
200
```

Size spec:

```
Red
Blue
Green
```

Brand spec:

```
250 GSM
300 mm
```

Material spec with color values:

```
Red
Blue
```

Also reject options that are:

Junk / gibberish

```
asdf
xxx
123abc
```

Test data

```
test
sample
demo
```

Placeholder values

```
NA
N/A
nil
-
.
unknown
```

Vague values

```
As per requirement
Customized
Standard
Other
General
Misc
```

Excessively long

```
length > 50 characters
```

Promotional text

```
Best Quality
Buy Now
www.example.com
```

If any of these apply → **REJECT**

---

# RULE 2 — STRONG SIGNALS

KEEP the option if any of the following are true:

Multi-source validation

```
signal_sources >= 2
```

Strong seller adoption

```
fill_rate >= 20
```

Strong buyer demand

```
prod_count >= 10
```

---

# RULE 3 — MODERATE VALID SIGNAL

If the option:

```
signal_sources == 1
```

AND the option is clearly **valid for the spec**, then **KEEP**.

Example:

```
impression > 0
but prod_count = 0 and fill_rate = 0
```

If the value is valid for the spec → KEEP.

---

# RULE 4 — MERGE DUPLICATE OPTIONS

MERGE when two options represent the **same value but formatted differently**.

Examples:

Formatting differences

```
3mm vs 3 mm
120GSM vs 120 GSM
```

Capitalization

```
blue vs Blue
```

Spelling variations

```
Aluminium vs Aluminum
```

When merging:

* Keep the **cleaner / more standardized option**
* The merge target **must already exist in the same spec**
* Do **not create new option values**

Example:

```
"3mm" → MERGE → "3 mm"
```

---

# RULE 5 — NO SIGNAL

Reject options with **no signal anywhere**.

```
prod_count = 0
fill_rate = 0
impression = 0
```

---

# IMPORTANT RULES

You MUST follow these strictly:

1. Evaluate **every option** from input.
2. Do **not modify option_value text**.
3. Do **not invent new options**.
4. MERGE only into **existing options within the same spec**.
5. Output must include **all specs and all options**.
6. Use **signals only from input**.
7. Decisions must be **consistent with rules above**.

---

# FINAL OPTION LIST

For each spec:

```
final_option_list =
all options with decision = KEEP
+
all merge target options
```

Rejected options must **not appear** in the final list.

---

# OUTPUT FORMAT (STRICT JSON ONLY)

No explanations.
No markdown.
Return valid JSON only.

```
{
  "mcat_id": <number>,
  "category_name": "<string>",
  "spec_decisions": [
    {
      "spec_name": "<exact spec name>",
      "options": [
        {
          "option_value": "<exact value>",
          "decision": "KEEP | REJECT | MERGE",
          "merge_into": "<target option if MERGE else null>",
          "reason": "ProdCount:X FillRate:Y Imp:Z SignalSources:N <short reason>"
        }
      ],
      "final_option_list": [
        "<kept options only>"
      ]
    }
  ]
}

--- Code Node: Parse & Build Final Specs ---
// ============================================================
// PARSE AUDIT OUTPUT + BUILD FINAL SPECS
// Extract LLM decisions, rebuild spec JSON with cleaned options
// ============================================================

const first = $input.first().json;
const llmOutput = first.outpu...

--- Code Node: Flatten Audit Rows ---
const data = $input.first().json;

const { mcat_id, category_name, spec_option_importance } = data;

const rows = [];

for (const spec of spec_option_importance || []) {

  const specName = spec.spec_name;

  for (const opt of spec.options || []) {

    rows.push({
      mcat_id,
      category_name...

--- Code Node: Code in JavaScript1 ---
// ============================================================
// JOIN OPTION NUMBERS — Use mapper name mapping to pull actual
// numbers from raw source data per option. LLM never touches numbers.
// ============================================================

function norm(v) {
  return (v ?? ''...

--- Code Node: Code in JavaScript2 ---
// -----------------------------------------------------
// SPLIT CURRENT OPTIONS AND NEW OPTIONS BY SPEC
// -----------------------------------------------------

const data = $input.first().json;

const audit = data.audit_table || [];

const currentSpecs = {};
const newSpecs = {};

// group rows b...

--- Code Node: Code in JavaScript3 ---
const data = $input.first().json;

const rows = [];

function processSpecs(specs, type) {
  for (const spec of specs) {
    for (const opt of spec.options) {
      rows.push({
        mcat_id: data.mcat_id,
        category_name: data.category_name,
        spec_type: type,
        spec_name: spec.s...

--- Code Node: Code in JavaScript4 ---
const input = $input.first().json;

const { mcat_id, category_name, current_specs } = input;

const specMap = {};

for (const spec of current_specs || []) {

  const specName = spec.spec_name;

  if (!specMap[specName]) {
    specMap[specName] = {
      spec_name: specName,
      options: []
    };
...

--- Code Node: Code in JavaScript ---
const input = $input.first().json;

const category = input.category_name;
const mappings = input.mappings;

const rows = [];

for (const spec of mappings) {

  const specName = spec.spec_name;

  // CURRENT OPTION MAPPINGS
  for (const map of spec.option_mappings || []) {

    const canonical = map....
