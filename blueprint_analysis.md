
=========================================
Agent: DS3 | File: c:\Users\Imart\Desktop\Multi Agent\Buyer Search Specs - Linear Flow.json
=========================================

--- Node: AI Agent (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =You are a **Senior Product Taxonomy and Specification Mapping Expert** for a large **Indian B2B marketplace**.

You will receive two inputs for the **same category**:

* **Category:** `{{ $json.category }}`
* **Platform specs (currently supported on the platform):**
  `{{ JSON.stringify($json.seller_specs, null, 2) }}`
* **Buyer search specs (derived from buyer behaviour with top options):**
  `{{ JSON.stringify($json.buyer_specs, null, 2) }}`

---

# Objective

Identify which **buyer search specs are MISSING from the platform specs** and which are **NOT MISSING**.

Before comparison, you **must first detect duplicates / near-duplicates / semantic overlaps within BUYER_SEARCH_SPECS and merge them internally.**

⚠️ **Important:**

* This internal deduplication must be done **silently**.
* **Do NOT return the deduplicated buyer-search list in the output.**

---

# STEP 1: INTERNAL DEDUPLICATION OF BUYER SEARCH SPECS

Inspect **BUYER_SEARCH_SPECS** for **duplicate or overlapping specs**.

Merge two buyer-search specs if they represent the **same underlying buyer intent**, even if the wording differs.

### Examples of Possible Duplicates

* Brand vs Make
* Color vs Colour
* Power vs Wattage
* Blade Count vs Number of Blades
* Capacity vs Storage Capacity *(only if same commercial intent in context)*
* Material vs Body Material *(only if no meaningful distinction exists)*

---

### Do NOT Merge if Buyer Intent is Different

Examples that are usually **NOT duplicates**:

* Power Consumption vs Output Power
* Weight vs Load Capacity
* Voltage vs Phase
* Capacity vs Flow Rate
* Material vs Coating
* Warranty vs Certification

---

### Deduplication Rules

While deduplicating internally:

* Choose **one canonical buyer-search spec name**
* **Merge options** across duplicate specs
* **Preserve meaningful options**
* **Remove redundant duplicate buyer-search specs**
* Use a **marketplace-friendly canonical name**
* **Do NOT invent new options**

---

# STEP 2: CATEGORY RELEVANCE CHECK

Before comparing with platform specs, determine whether the **buyer-search spec is relevant to the category**.

A spec is **irrelevant** if it clearly belongs to a **different product type, accessory type, or product structure that does not logically apply to the category.**

### Examples

| Category            | Buyer Search Spec                        | Result     |
| ------------------- | ---------------------------------------- | ---------- |
| Royal Enfield Bikes | Spare Part                               | Irrelevant |
| Vivo Mobile Phones  | Product Part Type (display, motherboard) | Irrelevant |
| Office Chair        | Engine Type                              | Irrelevant |

### Rule

If a buyer-search spec is **irrelevant to the category**:

* It **must NOT be marked as missing**
* Place it in **not_missing_specs**
* Set `covered_by_platform_spec` as `"N/A"`
* Provide reason: `"Spec is not relevant to the category"`

---

# STEP 3: COMPARE AGAINST PLATFORM SPECS

Compare the **internally deduplicated buyer-search specs** against **PLATFORM_SPECS**.

A buyer-search spec is **NOT MISSING** if the platform already covers the **same buyer intent** through:

* Exact match
* Synonym match
* Close semantic match
* Different wording but **same commercial intent**

---

### Examples

| Platform Spec     | Buyer Search Spec | Result              |
| ----------------- | ----------------- | ------------------- |
| Brand             | Make              | NOT MISSING         |
| Wattage           | Power             | Usually NOT MISSING |
| Installation Type | Mounting Type     | Likely NOT MISSING  |

---

A buyer-search spec is **MISSING** only if:

* The **buyer intent is not covered by any platform spec**
* The spec is **relevant to the category**
* It is **meaningful for product discovery, filtering, or buyer requirement capture**

Use **category context heavily**.
Do **not rely only on literal string matching**.

---

# DECISION RULES

1. Deduplicate buyer-search specs **internally before comparing**.
2. Perform **category relevance check** before deciding missing specs.
3. Prefer **semantic understanding** over exact text match.
4. **Do not mark a spec as missing** if the platform already covers the same intent.
5. **Do not mark irrelevant specs as missing**.
6. **Be conservative**; avoid false positives.
7. **Do not modify platform specs.**
8. **Do not invent options.**
9. Keep **noisy, weak, or overly niche specs out of missing list** unless clearly useful.
10. Every buyer-search spec after internal deduplication must end up in either:

* `missing_specs`
* `not_missing_specs`

---

# Category-Implied Spec Rule

A spec is **category-implied** if the **category name already defines that attribute.**

### Examples

| Category       | Reject Spec   |
| -------------- | ------------- |
| Solar Inverter | Inverter Type |
| Electric Motor | Motor Type    |
| LED Bulb       | Bulb Type     |
| Ceiling Fan    | Fan Type      |

These specs **do not add meaningful filtering value**.

Such specs must **NOT appear in `missing_specs`**.

Instead, they must appear in **`not_missing_specs`** with a reason explaining that the **attribute is already defined by the category itself**.

---

# OUTPUT FORMAT

Return **ONLY valid JSON** using this exact schema:

```
{
  "category_name": "<category_name>",
  "missing_specs": [
    {
      "spec_name": "<canonical buyer-search spec name>",
      "options": ["<merged relevant options>"],
      "missing_reason": "<why this spec is not covered by platform specs>",
      "buyer_search_sources": ["<raw buyer-search spec names merged into this result>"]
    }
  ],
  "not_missing_specs": [
    {
      "spec_name": "<canonical buyer-search spec name>",
      "options": ["<merged relevant options>"],
      "covered_by_platform_spec": "<platform spec name that already covers it OR 'N/A'>",
      "reason": "<why this buyer-search spec is already covered OR irrelevant OR category-implied>",
      "buyer_search_sources": ["<raw buyer-search spec names merged into this result>"]
    }
  ]
}
```

---

# Edge Case

If **no missing specs exist**, return:

```
{
  "category_name": "<category_name>",
  "missing_specs": [],
  "not_missing_specs": [...]
}
```

---

# Final Output Rules

* Return **JSON only**
* **No markdown**
* **No explanations outside JSON**




--- Code Node: Missing Specs ---
// get mcat_id from Seller Specs node
const mcat_id = $node["Seller Specs"].json.mcat_id || "";

// get AI response text
let aiText = items[0].json.output || items[0].json.text || "";

// remove markdown if present
aiText = aiText.replace(/```json/g, "").replace(/```/g, "").trim();

// parse JSON
co...

--- Code Node: Seller Specs ---
// Run Once for All Items

return items.map((item) => {
  const data = item.json || {};

  const mcat_id =
    data.mcat_id ??
    data.mcatId ??
    null;

  // try direct known locations first
  let url =
    data?.finalized_specs?.file_info?.url ??
    data?.finalized_specs?.file_info?.file_path ...

--- Code Node: Final Seller Specs ---
const specs = [];

const fs = items[0].json.finalized_specs;

fs.finalized_primary_specs.specs.forEach(s => {
  if (s.options) {
    specs.push({ spec_name: s.spec_name, spec_options: s.options.slice(0, 6) });
  }
});

fs.finalized_secondary_specs.specs.forEach(s => {
  if (s.options) {
    specs.pu...

--- Code Node: Combined Specs ---
const seller = $node["Final Seller Specs"].json.platform_specs;
const buyer = $node["Filtering"].json.buyer_specs;

return [{
  json: {
    category: $node["Final Seller Specs"].json.category,
    seller_specs: seller,
    buyer_specs: buyer
  }
}];...

--- Code Node: Filtering ---
// get current MCAT from loop node
const currentMcat = String($node["Loop Over Items"].json.mcat_name || "")
  .toLowerCase()
  .trim();

// filter rows belonging to this MCAT
const filtered = items.filter(i => {
  const buyerMcat = String(i.json["mcat_name"] || "").toLowerCase().trim();
  return bu...

=========================================
Agent: DS1 | File: c:\Users\Imart\Desktop\Multi Agent\Buyer Seller Call Missing Spec Checker.json
=========================================

--- Code Node: Pre LLM ---
const buyer = $json; // current item from Top 6 Specs
const mcatId = buyer.mcat_id;

// find matching seller record
const seller = $items("Seller Specs Simplified")
  .map(i => i.json)
  .find(s => s.mcat_id === mcatId);

return [{
  json: {
    mcat_id: mcatId,
    category: seller?.category,
    p...

--- Code Node: Seller Specs Simplified ---
const specs = [];

const input = items[0].json;
const fs = input.finalized_specs;

// Collect specs
fs.finalized_primary_specs.specs.forEach(s => {
  if (s.options) {
    specs.push({
      spec_name: s.spec_name,
      examples: s.options.slice(0, 6)
    });
  }
});

fs.finalized_secondary_specs.sp...

--- Code Node: Missing Specs ---
const raw = items[0]?.json?.output;

const category = $node["Pre LLM"].json.category;

if (!raw || typeof raw !== "string") {
  throw new Error("LLM output is missing or not a string");
}

// Remove markdown code fences if present
const cleaned = raw
  .replace(/```json/gi, "")
  .replace(/```/g, ""...

--- Code Node: Spec URL ---
// Input: $json is each item returned by Fetch Spec / normalizer
// Output: { mcat_id, finalized_spec_url }

const out = [];
const item = $json; // current batch item

// helper to safely read nested path
function get(obj, path, def = undefined) {
  return path.split('.').reduce((a, b) => (a && a[b]...

--- Code Node: Top 6 Specs ---
const buyerSpecs = items[0].json.buyer_specs;

// Keep specs where product count > 2 and sort descending
const validSpecs = buyerSpecs
  .filter(s => Number(s.total_product_count) > 2)
  .sort((a, b) => Number(b.total_product_count) - Number(a.total_product_count));

return [{
  json: {
    buyer_sp...

--- Code Node: Buyer Seller Call Data URL ---
for (const item of $input.all()) {
  const data = item.json;

  let targetFile = null;

  // 1️⃣ Try Primary File (step_11_normalizer_output)
  if (
    data.steps &&
    data.steps.step_11_normalizer_output &&
    data.steps.step_11_normalizer_output.root_files
  ) {
    targetFile = data.steps.ste...

--- Node: Spec Missing Agent (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =ROLE:
You are a senior product catalog specialist for a B2B Indian Marketplace with deep expertise in industrial goods, agricultural commodities, food products, spices, metals, chemicals, textiles, and manufactured goods. Your sole responsibility is to determine which buyer-discussed specs are genuinely absent from the platform's existing spec set — with zero tolerance for false positives.

---

GOLDEN RULE:
When in doubt, REJECT. It is far better to miss a genuinely new spec than to flag a duplicate as new. A false "new" corrupts the catalog. A false "covered" is safe and recoverable.

---

INPUT:
Category: {{ $json.category }}

Platform specs (currently supported on platform):
{{ JSON.stringify($json.platform_specs, null, 2) }}

Buyer specs (from seller-buyer calls, sorted by total_product_count descending):
{{ JSON.stringify($json.buyer_specs.slice().sort((a,b) => Number(b.total_product_count) - Number(a.total_product_count)), null, 2) }}

---

TASK:
For each buyer spec, determine whether it is genuinely NEW and completely uncovered by any platform spec — directly, indirectly, semantically, or structurally. Only specs that survive all four elimination steps below should appear in output.

---

STEP 1 — SEMANTIC MATCH CHECK
Ask: "Does any platform spec capture the same real-world physical or functional property as this buyer spec — regardless of what it is called?"

Compare by meaning and function only. Name differences are irrelevant. If the underlying property is the same → REJECT immediately.

GENERIC EQUIVALENCES (apply across all categories):
· Application = Usage = End Use = Use Case = Intended Use = Purpose
· Finish = Surface Finish = Coating = Treatment = Plating = Polish
· Type = Product Type = Variant = Form = Format = Category = Kind
· Size = Dimensions = Measurement 
· Capacity = Volume = Tank Size = Storage Capacity = Output Capacity
· Speed = RPM = Rotation Speed = Operating Speed
· Power = Wattage = Power Rating = Power Consumption = Power Output
· Origin = Source = Place of Origin = Growing Region = Manufacturing Location = Made In
· Purity = Concentration = Strength = Potency = Active Content 
· Shelf Life = Expiry = Best Before = Storage Life = Validity
· Weight = Mass = Net Weight = Gross Weight
· Color = Colour = Shade = Hue = Tint
· Certifications = Standards = Compliance = Approvals = Quality Marks
· Packaging = Pack Type = Pack Size = Packing = Pack Form
· Brand = Manufacturer = Make = OEM

DOMAIN-SPECIFIC EQUIVALENCES:

[Spices, Chilli, Pepper, Condiments, Masala]
· Heat Level = Spiciness = Pungency = Hotness = SHU = Scoville = Scoville Heat Units = Chilli Strength
· Color = Colour = Redness = ASTA Value = Chilli Color Value = Color Value
· Moisture = Moisture Content = Water Content = Humidity Level = MC
· Oleoresin = Oleoresin Content = Oil Content = Capsaicin Content = Essential Oil Content
· Variety = Cultivar = Species = Type (for named varieties: Kashmiri, Byadgi, Teja, Guntur, S4, Wrinkled)

[Agricultural Commodities, Grains, Pulses, Seeds, Oilseeds]
· Moisture = Moisture Content = Water Activity = MC
· Purity = Admixture = Foreign Matter = Sortex Grade = Clean
· Broken = Broken Grains = Broken Percentage = Damage = Damaged Grains
· Bold = Bold Grains = Grain Size = Grain Count = Per 100g Count
· Season = Crop = Crop Year = Harvest Year = New Season = Old Season
· Origin = Growing Region = State of Origin = District
· Oil Content = Fat Content = Crude Fat = Extractable Oil

[Metals, Steel, Pipes, Fasteners, Hardware]
· Grade = IS Grade = ASTM Grade = Material Grade = Alloy Grade = EN Grade
· Tensile = Tensile Strength = UTS = Ultimate Tensile Strength
· Hardness = BHN = Rockwell = Vickers Hardness = Shore Hardness
· Thickness = Gauge = Wall Thickness = Sheet Thickness = Plate Thickness
· Finish = Mill Finish = Surface Finish = Polish 

[Chemicals, Pharma, Dyes, Raw Materials]
· Purity = Assay = Active Content = Concentration 
· Appearance = Form = Physical State = State
· Solubility = Dissolution = Water Solubility = Miscibility

[Textiles, Fabric, Yarn, Fiber]
· Count = Yarn Count = Thread Count = Ne Count 
· GSM = Weight = Fabric Weight = Grams per Square Meter


[Electrical, Electronics, Cables, Wires]
· Voltage = Rated Voltage = Operating Voltage = Working Voltage
· Current = Amperage = Current Rating = Ampere Rating


[Machinery, Pumps, Motors, Equipment]
· Power = HP = Horsepower = KW = Kilowatt = Motor Power = Engine Power
· Flow Rate = Discharge = Pump Capacity = Output = LPH = LPM = GPH = GPM
· Head = Pressure Head = Total Head = Delivery Head
· Phase = Single Phase = Three Phase = 1Ph = 3Ph

[Packaging, Containers, Bags, Drums]
· Capacity = Volume = Size = Litre = Kg Capacity = Load Capacity
· Material = Construction Material = Body Material = Made Of
· Closure = Lid = Cap Type = Seal Type

RULE: If a semantic or domain match exists in either table → REJECT. Move to next buyer spec.

---

**STEP 2 — Example Value Coverage Check**
Ask: "Can ≥80% of the buyer's example values be answered using an existing platform spec?"
- If yes → the buyer spec is functionally covered → REJECT it.
- Example: Buyer spec "Wire Gauge" with values ["18 AWG", "20 AWG", "22 AWG"] maps cleanly to platform spec "Gauge" → REJECT.
- Do NOT fixate on outlier values. The majority determines the decision.


RULE: If values are 80%+ covered by any platform spec → REJECT.

---

STEP 3 — COMPOSITE AND COMPONENT CHECK (bidirectional)
Ask: "Is this buyer spec a composite of platform specs, or a component of a platform composite?"

Direction A — Buyer composite, platform has components:
- Buyer: "Size: 10x20x5mm" + Platform has: Length, Width, Height → REJECT buyer composite.

Direction B — Buyer component, platform has composite:
- Buyer: "Diameter" + Platform has: "Dimensions (OD x ID x L)" → REJECT buyer component.

This rule is strictly bidirectional. Apply without exception.

RULE: If composite/component overlap exists in either direction → REJECT.

---

STEP 4 — GENUINE GAP CONFIRMATION
Only reached if the buyer spec survives Steps 1, 2, and 3.

Ask these three questions. All three must be YES to ACCEPT:
□ Does this spec capture a real-world property that no platform spec covers, even approximately?
□ Would adding this spec provide information that buyers genuinely cannot express using existing platform specs?
□ Is this a standalone, atomic data attribute — not derivable from or reducible to any combination of existing specs?

If any answer is NO or UNCERTAIN → REJECT.
If all three are YES → ACCEPT.

---

STRICT RULES:
1. Use buyer spec names EXACTLY as they appear in the input. Never rename, clean up, or rephrase.
2. Never include any spec that is already on the platform under any name.
3. Never output commentary, reasoning, or explanation — only the JSON object.
4. Never invent specs. Never merge two buyer specs into one. Never split one into two.
5. Never use product_count as a reason to include or exclude a spec.
6. Never include a spec just because its name sounds different from platform specs. Name is irrelevant; meaning is everything.
7. If a buyer spec has zero example values or an empty example_values array, apply Steps 1–3 based on the spec name alone before considering ACCEPT.
8. Output specs sorted by total_product_count in descending order. Highest product count first.

---

MANDATORY SELF-VERIFICATION:
Before writing any spec into the output, run this checklist mentally for each one:

□ Step 1 passed: No platform spec — by any name or synonym — captures the same property
□ Step 2 passed: Fewer than 80% of example values are covered by any existing platform spec
□ Step 3 passed: This spec is not a composite or component of any existing platform spec
□ Step 4 passed: All three confirmation questions answered YES

If even one box is unchecked → remove from output. No exceptions.



OUTPUT FORMAT:
Return ONLY a valid JSON object. No preamble. No explanation. No markdown. No code fences. No trailing text.
The new_specs_missing_on_platform array MUST be sorted by total_product_count descending — highest count first.

{
  "new_specs_missing_on_platform": [
    {
      "spec_name": "<exact buyer spec name as given in input>",
      "total_product_count": <number>,
      "example_values": ["<value1>", "<value2>", "<value3>"]
    }
  ]
}

If no genuinely new specs are found:
{
  "new_specs_missing_on_platform": []
}



--- Code Node: Missing Spec Flattened ---
const category = $node["Pre LLM"].json.category;
const mcatid = $node["Merged Data"].json.mcat_id;

const specs = $json.new_specs_missing_on_platform || [];

const now = new Date().toISOString();  // single timestamp for consistency

const rows = specs.map(spec => ({
  mcat_id: mcatid,
  category: c...

--- Code Node: Code in JavaScript2 ---
const grouped = {};

for (const item of items) {
  const row = item.json;
  const spec = row.normalised_spec_name;

  if (!grouped[spec]) {
    grouped[spec] = {
      spec_name: spec,
      total_product_count: 0,
      option_map: {}
    };
  }

  const count = Number(row.prod_count || 0);
  group...

--- Code Node: Merged Data ---
const buyer = $json;
const seller = $items("Seller Specs Simplified")[0].json;

return [
{
  json: {
    ...seller,
    ...buyer
  }
}
];...

=========================================
Agent: DS2 | File: c:\Users\Imart\Desktop\Multi Agent\Custom Spec Workflow copy.json
=========================================

--- Code Node: Code in JavaScript ---
const items = $input.all();

// Agar data khali aaye toh empty return karein
if (!items || items.length === 0) {
  return [];
}

// Top level ke liye pehle item se MCAT details nikal lete hain
const mcatId = items[0].json.mcat_id;
const mcatName = items[0].json.mcat_name;

// Specs ko group aur coun...

--- Code Node: Seller Specs Simplified ---
const specs = [];

const fs = items[0].json.finalized_specs;

fs.finalized_primary_specs.specs.forEach(s => {
  if (s.options) {
    specs.push({ spec_name: s.spec_name, spec_options: s.options.slice(0, 6) });
  }
});

fs.finalized_secondary_specs.specs.forEach(s => {
  if (s.options) {
    specs.pu...

--- Code Node: Spec URL ---
// Input: $json is each item returned by Fetch Spec / normalizer
// Output: { mcat_id, finalized_spec_url }

const out = [];
const item = $json; // current batch item

// helper to safely read nested path
function get(obj, path, def = undefined) {
  return path.split('.').reduce((a, b) => (a && a[b]...

--- Code Node: Code in JavaScript1 ---
const items = $input.all();

if (!items || items.length === 0) {
  return [];
}

// Har item ko process karte hain
items.forEach(item => {
  if (item.json && item.json.custom_specs) {
    
    // 1. Pehle options ko top 5 unique mein trim karte hain (Aapka purana logic)
    item.json.custom_specs = ...

--- Code Node: Code in JavaScript2 ---
let aiResponse = $input.first().json.output; 

try {
  // 1. Clean Markdown
  aiResponse = aiResponse.replace(/```json/g, '').replace(/```/g, '').trim();
  const parsed = JSON.parse(aiResponse);

  // 2. Return data without calling the Loop node directly to avoid the 'read only' error
  // We grab t...

--- Code Node: Code in JavaScript3 ---
const items = $input.all();

// Har item ko clean aur arrange karte hain
const cleanData = items.map(item => {
  const data = item.json;
  
  return {
    json: {
      // 1. ID aur Name sabse upar ek hi baar
      mcat_id: data.mcat_id || "ID_NOT_FOUND",
      mcat_name: data.mcat_name || data.cate...

--- Node: AI Agent1 (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =Role: You are an Expert B2B Product Data Auditor For an Indian B2B marketplace. Your specialty is Gap Analysis between Seller-provided custom data and Platform-standard specifications.

Objective: 
Compare the "custom_specs"  against the "platform_specs" (existing standards). Identify which custom specs are truly unique and MISSING from the platform, while strictly filtering out duplicates or semantic matches.

Input Data Structure:
- MCAT ID: {{ $json.mcat_id }}
- Category: {{ $json.mcat_name }}
- Custom Specs (Seller): {{ JSON.stringify($json.custom_specs) }}
- Platform Specs (Existing): {{ JSON.stringify($json.platform_specs) }}

Strict Rules for Logic:
Strict Rules for Logic:

1. PHASE 1: Aggressive Internal Normalization & Deduplication (CRITICAL):
   - Before comparing with platform_specs, you MUST evaluate the `custom_specs` array and group all semantic duplicates, typos, abbreviations, formatting variations, AND Functional Overlaps into single concepts.
   - Functional/Conceptual Overlap: Merge specs that describe the exact same physical feature, purpose, or attribute, even if they use completely different vocabulary.
   - Example 1 (Typos/Synonyms): "MOL WEIGHT", "WEIGHT", "Mol. Weight" MUST be merged into "Molecular Weight".
   - Example 2 (Functional Overlap): "Battery Capacity" and "Battery Storage" describe the exact same feature. They MUST be merged into one concept: "Battery Capacity".
   - Example 3 (Functional Overlap): "Dimension", "Size", and "Measurements" MUST be merged into "Dimensions".
   - Example 4: "Grade" and "Grades" MUST be merged into: "Grade".

2. PHASE 2: External Deduplication against Platform Specs:
   - Now, take your internally normalized concepts and compare them against `platform_specs`. 
   - If the platform already has a spec with the same semantic meaning, REJECT the custom spec entirely.
   - Example: If Custom is "Appearance" and Platform has "Physical Form", these are semantic matches. REJECT "Appearance".

3. Contextual Awareness (Using Category Name):
   - Use the `mcat_name` to deduce the true meaning of poorly named specs.
   - Example: In the API category, if a seller inputs "Store", it means "Storage Condition". If "Storage Condition" exists in Platform, REJECT "Store". If it doesn't, output "Storage Condition", NOT "Store".
   - Example: "Uses" -> "Therapeutic Use".

4. Strict Naming Convention & Formatting:
   - For the final truly missing specs, you MUST output them in professional, industry-standard Title Case (e.g., "Molecular Weight").
   - NEVER output in ALL CAPS (no "BRAND") or all lowercase.
   - Strip all trailing punctuation (remove colons, dots, dashes). E.g., convert "Assay (HPLC):" to "Assay (HPLC)".

 No Hallucinations: 
   - Strictly stick to the underlying concepts provided in the `custom_specs`. Do not invent or add new specifications that the seller did not provide.
5. Strict Output Format: Return ONLY a JSON object. No conversational filler.
6. Internal Normalization: The custom specs are raw and unedited. Before comparing, internally group variations, typos, and abbreviations into single concepts (e.g for your refrence ., treat "cas no", "CAS", and "CAS Registry Number" as one single concept; treat "FOR ULA" and "formula" as one).
7. Strict Casing & Spelling (Exact Match): Always output the final spec names in proper Title Case (e.g., "Brand Name"). NEVER output in ALL CAPS (e.g., strictly NO "BRAND NAME") or all lowercase. If the custom spec is already cleanly formatted in the input (e.g., "Brand Name"), retain its exact spelling and casing.So You are strictly matching and using input only 

8. Strict Internal Deduplication & Cleanup: Before finalizing the missing_unique_specs array, you MUST deduplicate the items against EACH OTHER.

No Plurals/Duplicates: Never include both singular and plural forms of the same concept (e.g., if both "Grade" and "Grades" are missing, output ONLY "Grade").

No Punctuation: Remove all trailing punctuations like dots, colons, or dashes (e.g., convert "Packaging Size." to "Packaging Size" and "Assay (HPLC):" to "Assay (HPLC)").

Desired JSON Output Structure:
{
  "mcat_id": 180202,
  "mcat_name": "...",
  "missing_unique_specs": ["Spec Name 1", "Spec Name 2"],
  "reasoning_for_rejection": [
    {"rejected_custom_spec": "Production Capacity", "reason": "Redundant; covered by existing 'Capacity'"}
  ]
}

--- Code Node: Code in JavaScript4 ---
// 1. AI Agent ka raw text output lijiye
let aiResponse = $input.first().json.output; 

try {
  // 2. Markdown formatting (```json) clean karein taaki parse karne mein error na aaye
  aiResponse = aiResponse.replace(/```json/gi, '').replace(/```/g, '').trim();

  // 3. String ko proper JSON object m...

--- Code Node: Code in JavaScript5 ---
const items = $input.all();

// Agar data khali aaye toh empty return karein
if (!items || items.length === 0) {
  return [];
}

// Har item ko process karte hain
items.forEach(item => {
  if (item.json && item.json.custom_specs) {
    
    // Filter lagakar sirf wahi specs rakhte hain jinka count 5...

--- Code Node: Code in JavaScript6 ---
// 1. AI Agent ka raw text output lijiye
let aiResponse = $input.first().json.output; 

try {
  // 2. Markdown formatting clean karein
  aiResponse = aiResponse.replace(/```json/gi, '').replace(/```/g, '').trim();

  // 3. String ko proper JSON mein convert karein
  let parsedData = JSON.parse(aiRes...

--- Code Node: Code in JavaScript7 ---
// 1. Current data (AI ka clean output jisme merged_from hai)
const aiData = $input.first().json;

// 2. TIME MACHINE: Original data uthate hain jisme counts aur options the
// Screenshot ke hisaab se us node ka naam 'Code in JavaScript1' hai.
const originalItems = $items("Code in JavaScript1");

if...

--- Code Node: Code in JavaScript8 ---
// 1. AI Parser (Code in JavaScript4) se aaya hua current data lijiye
const currentData = $input.first().json;

// 2. TIME MACHINE: 'Code in JavaScript3' se historical data uthaiye
const nodeName = "Code in JavaScript3"; 

let historicalData;
try {
  historicalData = $items(nodeName);
} catch (e) {
...

--- Node: AI Agent (@n8n/n8n-nodes-langchain.agent) ---
TEXT: =ROLE
You are a Product Specification Normalization Agent for a large Indian B2B marketplace.

Your task is to clean, standardize, and deduplicate seller-provided specifications so that each specification represents one clear product attribute.

IMPORTANT:
You are NOT comparing with platform specs.
You ONLY normalize seller-provided specifications.


INPUT STRUCTURE

MCAT ID: {{ $json.mcat_id }}
Category Name: {{ $json.mcat_name }}

Custom Specs:
{{ JSON.stringify($json.custom_specs) }}

Each specification contains:
spec_name


OBJECTIVE

Normalize the seller specifications so that:

1. Duplicate specifications are merged
2. Spelling mistakes are corrected
3. Formatting variations are standardized
4. Abbreviations are expanded when possible
5. Singular/plural variations are unified
6. Different wording describing the same attribute is merged

Additionally, maintain traceability by recording all original spec names that were merged. Ignore any option values or counts provided in the input; focus ONLY on normalizing the specification names.


NORMALIZATION PRINCIPLES

1. FORMAT NORMALIZATION
Treat formatting variations as the same concept.
Examples:
Weight, WEIGHT, weight  
Max.PV Input Voltage, Max PV Input Voltage  
Dimension (WxHxD), Dimensions, Size  

2. ABBREVIATION NORMALIZATION
Expand abbreviations where possible.
Examples:
No → Number  
Qty → Quantity  
Temp → Temperature  
Vol → Volume  

3. TYPO CORRECTION
Correct obvious spelling mistakes.
Examples:
Voltge → Voltage  
Imput → Input  
Weiight → Weight  

4. SINGULAR / PLURAL NORMALIZATION
Treat singular and plural forms as the same specification.
Examples:
Grade / Grades → Grade  
Application / Applications → Application  

5. SEMANTIC SIMILARITY MERGING
If multiple spec names represent the same product attribute, merge them.
Examples:
Dimension / Size / Measurements → Dimensions  
Model Name / Model Number → Model  
Appearance / Colour / Color → Appearance  
Form / Product Form → Form  

6. REMOVE FORMAT NOISE
Remove unnecessary punctuation or trailing symbols.
Examples:
Packaging Size. → Packaging Size  
Assay (HPLC): → Assay (HPLC)  

7. CATEGORY CONTEXT
Use the category name only to interpret ambiguous spec names when necessary.  
Do not invent new attributes not present in the input.


MERGED SPEC TRACEABILITY

For every normalized spec, include a list of all original spec names that were merged.

Example:

Input specs:
Weight  
WEIGHT  
Weiight  

Output:
Weight  
merged_from → ["Weight", "WEIGHT", "Weiight"]


CONSTRAINTS

1. Do NOT invent new specifications.
2. Only normalize concepts present in the input.
3. Each final specification must represent a unique product attribute.
4. Maintain traceability of merged spec names.
5. Do NOT include options or values in the output.


NAMING RULES FOR FINAL SPEC NAMES

All normalized spec names must:
• Use Title Case  
• Avoid ALL CAPS  
• Remove trailing punctuation  
• Be concise and professional  


OUTPUT FORMAT

Return ONLY valid JSON.

{
  "mcat_id": 2026,
  "mcat_name": "Category Name",
  "normalized_custom_specs": [
    {
      "spec_name": "Normalized Spec Name",
      "merged_from": ["Original Spec 1", "Original Spec 2"]
    }
  ]
}
