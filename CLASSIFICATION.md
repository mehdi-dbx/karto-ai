# KARTO Classification — two axes

Every AI deployment sits at ONE intersection of two axes. It is a grid, not a flat list.

## Axis 1 — VERTICAL (what industry the company is). A company has exactly one.
1. Financial Services
2. Insurance
3. Legal & Professional Services
4. Healthcare & Life Sciences
5. Media / Entertainment / Gaming
6. Retail & E-commerce
7. Manufacturing & Robotics
8. Education
9. Government / Public Sector
10. Energy & Utilities
11. Logistics & Supply Chain
12. Agriculture
13. Telecom
14. Real Estate & Construction
15. Travel & Hospitality
16. Technology (soft — software, cloud, IT services, "Information Technology"). Hardware/chipmakers stay in Manufacturing.
17. Mining & Materials (metals, diamonds, coal, raw extraction)

**STANDING RULE (extensible):** when a real cluster of companies doesn't fit existing verticals,
MINT A NEW VERTICAL rather than force-fit or leave unmapped. Always preserve the original label
in a `raw_sector` column — best-effort primary `vertical` + full transparency, nothing lost.
Hard-vs-soft split: "makes AI chips/rock" → Manufacturing/Mining; "writes AI software" → Technology.

## Axis 2 — HORIZONTAL (what the AI actually does). Cuts across all verticals.
- Software / Code
- Customer Support
- Sales / Marketing / Content
- Back-office (finance, HR, procurement)
- Cybersecurity
- **Core / Domain-specific** — the vertical's OWN work (bank fraud, pharma drug discovery,
  factory predictive-maintenance, grid optimization). Not transversal — belongs to the industry.

## The rule
- Deployment = (Vertical, Horizontal) coordinate. e.g. a bank chatbot = (Financial Services, Customer Support);
  a bank fraud model = (Financial Services, Core/Domain).
- One deployment = one cell. Never force it to choose between an industry and a function — it has both.
