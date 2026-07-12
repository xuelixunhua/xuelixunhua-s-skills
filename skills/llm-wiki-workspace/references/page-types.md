# Page Types

Use these page types as a default vocabulary. Adapt names to the domain if needed.

## `sources/`

For one source at a time.

Good fit:

- one report
- one article
- one PDF
- one interview transcript
- one spreadsheet export

Typical content:

- what the source is
- what it says
- what facts seem durable
- what should be promoted elsewhere
- what is uncertain or conflicts with prior knowledge

## `topics/`

For recurring subject areas that accumulate evidence from many sources.

Good fit:

- electricity spot market design
- storage economics
- transmission congestion
- policy evolution

## `entities/`

For named things or stable objects in the domain.

Good fit:

- regions
- companies
- plants
- policy programs
- datasets
- key concepts with a stable identity

If the domain is not entity-heavy, keep this folder small rather than forcing content into it.

## `synthesis/`

For analysis that combines multiple pages and is worth keeping.

Good fit:

- a comparison memo
- a framework
- a thesis update
- a major Q&A result worth preserving

If the workspace already has a master note, that note can function as the top synthesis page.

## Vertical knowledge-base files

For vertical knowledge bases, prefer human-readable three-layer files before creating a `domain/` control folder.

Default fit:

- `【第三层】<Domain>.md`: recomposed domain body and first reading target
- `【索引】<Domain>资料索引.md`: material index and source lineage
- `01-第一层-底层资料/`: raw or bottom-layer material
- `02-第二层-类型整理/`: compressed or type-organized notes
- `03-第三层-二次整理/`: optional folder for multiple third-layer notes

Optional fit:

- `【应用】<Domain>调用说明.md`
- `【案例】<Domain>案例库.md`
- `【问题】<Domain>开放问题.md`
- `wiki/domain/` only when a large workspace truly needs separate machine-facing control pages

Do not create source maps, concept maps, mechanism maps, trigger maps, or playbooks by default when one stronger main note plus a material index would be clearer.
