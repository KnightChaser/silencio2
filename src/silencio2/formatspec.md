# **Silencio2 Format Specification**

## 1. Inventory File

**Purpose:** Maintain the catalog of sensitive items and their redaction metadata.

Each inventory entry includes:

* **id** (integer, > 0) — unique identifier for the item
* **code** (string) — classification code, e.g., `(1)(A)(c)`
* **desc** (string) — human-readable description, e.g., “email address”
* **surface** (string) — canonical example of the sensitive text, e.g., `kal@hacker.one`
* **aliases** (list) — alternative surfaces that map to the same item
* **scope** (string) — either `global` or `file-local` indicating reuse scope

### Example snippet:

```json
{
  "items": [
    {
      "id": 1,
      "code": "(1)(A)(c)",
      "desc": "email address",
      "surface": "kal@hacker.one",
      "aliases": [
        { "id": 1, "surface": "kal_sub@hacker.one" }
      ],
      "scope": "global"
    },
    {
      "id": 2,
      "code": "(1)(A)(c)",
      "desc": "email address",
      "surface": "jane@hacker.one",
      "aliases": [],
      "scope": "global"
    }
  ]
}
```

**Note:**

* The `surface` is the canonical form used when un-redacting.
* Each alias has its own alias ID and surface.
* Items marked `global` are applied across all files; `file-local` items may apply to a single document.

---

## 2. Badge Import File Format

**Purpose:** Allow users (or LLM outputs) to define new redaction items via a simple text file, one line per item.

Supported formats (two variants):

### 2.1 ARROW Format

```
[REDACTED: <code>, <desc>] => <surface>
```

**Explanation:**

* `<code>`: classification code, e.g., `(3)(A)(b)`
* `<desc>`: description, e.g., “api key”
* `=>` separates the badge from the concrete surface value
* `<surface>`: the exact text to match in documents, e.g., `AKIAIOSFODNN7EXAMPLE`

**Example:**

```
[REDACTED: (3)(A)(b), api key] => AKIAIOSFODNN7EXAMPLE
```

### 2.2 PIPE Format

```
<code> | <desc> | <surface>
```

**Explanation:**

* Same fields as ARROW format
* Uses `|` separators instead of `=>`

**Example:**

```
(3)(A)(b) | api key | AKIAIOSFODNN7EXAMPLE
```

### Parsing rules + error conditions:

* Lines starting with `#` or blank lines are ignored (comments)
* If neither format matches, the import process reports an error with the line number
* Duplicate surfaces with the same code and description merge into the same item

---

## 3. Redaction Tag Format

**Purpose:** Mark redacted spans in documents so that they can be restored (un-redacted) later, preserving which alias was matched.

**Tag syntax:**

```
[REDACTED(#<item_id>|var=<variant>): <code>, <desc>]
```

**Where:**

* `<item_id>`: integer referencing the inventory item
* `var=<variant>`:

  * `c` indicates the canonical surface matched
  * `aN` indicates alias with ID N matched
* `<code>` and `<desc>` echo classification and description exactly as defined
* Tag encloses entire matched span (surface is replaced with the tag)

**Examples:**

```
[REDACTED(#1|var=c): (1)(A)(c), email address]
[REDACTED(#1|var=a1): (1)(A)(c), email address]
```

**Behaviour:**

* When un-redacting, the tool uses the `item_id` and `variant` to restore exactly the surface text (canonical or alias)
* Tags inside code fences are skipped by default (unless explicitly allowed)
* The tag is *only* inserted once for each matched span; overlapping matches are resolved via “leftmost-longest” strategy to avoid nested/conflicting tags

---

## 4. CLI Tool Contract for local testing

All behaviors are defined at `cli.py`.

**Commands:**

* `init`: Create a new empty inventory file.
* `import_badges <badges.txt>`: Read badge import file, update inventory.
* `list_items`: Enumerate items in inventory with ID, code, desc, aliases.
* `alias add <item_id> <alias_surface>`: Add a new alias to an item.
* `alias list <item_id>`: List aliases for a given item.
* `redact <src_dir> <dst_dir> [--overwrite]`: Redact all `.md` files in `src_dir`, output to `dst_dir`.
* `unredact <src_dir> <dst_dir> [--overwrite]`: Reverse redaction tags back into original surfaces.

**Flags & behaviour:**

* `--overwrite`: allow target directory to already exist (otherwise abort)
* Default behaviour: skip files in code fences for redaction; dry-run flag (planned) may preview without writing
* Reports: number of matches per file, total matches

---

## 5. Behavioural Rules & Conventions

* **Global vs file-local scope:** Items tagged `global` can appear/redacted across all documents; `file-local` items apply only to their respective document context.
* **Canonical vs alias matching:** Inventory has a canonical surface and possibly multiple alias surfaces. Matching uses both but retains the variant tag so restoration is exact.
* **Idempotency:** Running `redact` multiple times on the same raw input must not re-tag already redacted spans (tags are masked).
* **Reversibility guarantee:** Provided inventory hasn’t changed, `unredact(redact(raw)) == raw` (modulo tag removal).
* **Format evolution:** Inventory, badge formats and tag syntax may evolve; version should be bumped and documented if incompatible changes occur.

---

## 6. Versioning & Compatibility

* This document corresponds to **Silencio2 v0.1.0** format.
* If breaking changes occur in tag syntax or inventory layout, update version (e.g., v0.2.0) and provide migration notes (e.g., “old tag format without `|var=` will still be accepted but map to canonical surface only”).

---

## 7. Examples

### Inventory snippet:

```json
{
  "items": [
    {
      "id": 5,
      "code": "(3)(A)(b)",
      "desc": "API key",
      "surface": "AKIAIOSFODNN7EXAMPLE",
      "aliases": [
         { "id": 1, "surface": "AKIAIOSFODNN7EXAMPLE-alt" }
      ],
      "scope": "global"
    }
  ]
}
```

### Badge import file (badges.txt):

```
# API keys
[REDACTED: (3)(A)(b), API key] => AKIAIOSFODNN7EXAMPLE
(3)(A)(b) | API key | AKIAIOSFODNN7EXAMPLE-alt
```

### Redacted Markdown snippet:

```
Here is the API key: [REDACTED(#5|var=c): (3)(A)(b), API key]

Alternatively you might see: [REDACTED(#5|var=a1): (3)(A)(b), API key]
```

### Unredacted result:

```
Here is the API key: AKIAIOSFODNN7EXAMPLE

Alternatively you might see: AKIAIOSFODNN7EXAMPLE-alt
```