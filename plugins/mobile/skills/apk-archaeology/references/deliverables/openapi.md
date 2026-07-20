# OpenAPI/Swagger v3 — Network Contract Recipe

**What this is.** The recipe for the per-feature loop's step 2, "Network contract"
(`../cognitive-sequence.md`; `../../SKILL.md` loop step 2): turning a feature's endpoint
slice into an OpenAPI v3 `.yaml`. Marked `spec pendente` in both of those files until this
recipe existed — this is that spec.

## Input — per-route variant

Loop step 1 (Route) already decided `native | WebView | blind` for this feature before this
step runs. That decision is what this recipe takes as input:

- **Native route:** the feature's slice of `data/endpoints.json` — every entry produced by
  Foundation step 3 (`extract_endpoints.py`) whose `file` falls under the partition's
  package prefix. Each entry is `{url, file, line, tag}` — a redacted URL literal plus an
  anchor and a bucket (`business` | `unclassifiable`). No HTTP verb, no params, no response
  shape: those are recovered by reading the source at `file:line` (Method, below), not
  emitted by the extractor.
- **WebView route:** there is no Foundation slice to draw on — the endpoint slice is empty
  by construction (`../cognitive-sequence.md`, "Feature ≠ partition"). The input is a
  **Fetch-tap** capture instead: the SPA hosted in the Flutter host used as harness, its
  network calls observed live (`../cognitive-sequence.md`, "The WebView branch"). Until
  that tap runs, there is no input at all — see Honesty stamp, below.
- **`blind` route:** no static or WebView reach for this feature. Do not produce an
  `openapi.yaml` for it — a file for a `blind` feature would dress a blind spot as an
  artifact. Mark the feature `blind` in the dossier instead and stop here.

## Output

`features/<slice>/openapi.yaml` — one OpenAPI v3 file per feature (the loop's scope is
per-feature, not one app-wide spec). `<slice>` is the feature/partition name used by the
loop's dispatch.

## Method — endpoints.json → paths/components

`endpoints.json` gives three mechanical facts per hit: the **URL literal** (secrets already
redacted by the extractor), a **file:line** anchor, and a **tag** (never treat
`unclassifiable` as business logic — the loop's inviolable rule applies here too). That is
raw material, not a finished contract. Turning it into OpenAPI paths/components is
**synthesis over the slice**, not another extraction pass:

1. **Group by base path.** Endpoints sharing a prefix (`/v1/items`, `/v1/items/{id}`) become
   one `path` item with multiple operations, or sibling path items — group the way the
   source groups them (same Retrofit interface / same OkHttp client), not by string
   similarity alone.
2. **Recover the HTTP verb** by opening `file:line` and reading the call site: a Retrofit
   `@GET`/`@POST`/`@PUT`/`@DELETE` annotation, or an OkHttp `Request.Builder().method(...)`
   call. **Known ceiling:** under obfuscation, Retrofit's `@retrofit2.http.*` annotations may
   not survive with RUNTIME retention — R8 can strip them, and a prior run on this method
   found exactly one file referencing `retrofit2.` with zero surviving `@retrofit2.http.*`
   annotations. When the annotation is gone, the verb is **not recoverable from static
   reach**: mark it `unknown`, never default to `GET` as a guess.
3. **Recover path/query params** the same way — `@Path`/`@Query`/`@Body` annotations, or
   `HttpUrl.Builder().addQueryParameter(...)` calls, anchored at the same `file:line`. A
   param name that appears literally in code (`@Path("id")`) is 🟢; a segment built from a
   variable with no literal name nearby stays ⬜ — do not invent a name for it.
4. **Recover response shape where visible** — a Retrofit return type (`Call<ItemDto>`) or a
   Moshi/Gson-annotated class near the call site gives field names and types 🟢. If no such
   class is in reach, the response schema is ⬜: emit an open schema
   (`additionalProperties: true`), not a guessed one.
5. **Runtime-assembled URLs are a bounded blind spot — evidenced, not hypothetical.** A base
   URL built at runtime (from `BuildConfig`, remote config, or concatenation against a value
   that isn't a single literal) will not appear as one match in `endpoints.json` — the
   extractor only captures a string that is wholly a URL literal in one place. A prior real
   run hit exactly this: **>99% readable code, yet Dimension B under-delivered because the
   real URLs were assembled at runtime against a vendor domain, not literals in code**
   (`../method.md`, "readable ≠ reachable"). When you see a partial literal (a path suffix
   with no scheme/host) or a `BuildConfig.BASE_URL + "..."` concatenation, do not complete
   the URL yourself — anchor what is literal, mark the host/base ⬜, and record it as a blind
   spot in the dossier rather than silently filling it from the harvest's BuildConfig entry
   as if it were the same fact.

### Origin stamp — mark every field

| Field | Stamp | Why |
|---|---|---|
| Path template (literal segments) | 🟢 literal | Verbatim in `endpoints.json`/source, anchored `file:line`. |
| HTTP verb (annotation present) | 🟢 literal | Read off `@GET`/`@POST`/etc. at the call site. |
| HTTP verb (annotation stripped/absent) | ⬜ runtime | Not recoverable statically — mark `unknown`, never guess. |
| Param names (literal in code) | 🟢 literal | `@Path("id")`, `@Query("page")`. |
| Param values | ⬜ runtime | Static gives the shape, never the value actually sent. |
| Response schema (DTO class in reach) | 🟢 literal | Field names/types from the Java/Kotlin class. |
| Response schema (no DTO in reach) | ⬜ runtime | Left open (`additionalProperties: true`) — don't guess fields. |
| Error contract (4xx/5xx bodies) | ⬜ runtime | Never data in the bytecode — only a dynamic capture or the Fetch-tap observes it. |
| Base URL / host (runtime-assembled) | ⬜ runtime | See point 5 above — documented, evidenced gap, not a hypothetical one. |

## Minimal worked example

Input — a 2-endpoint slice of `data/endpoints.json` (generic `telecorp` domain,
redacted-clean):

```json
{
  "endpoints": [
    {
      "url": "https://api.telecorp.example/v1/items",
      "file": "com/telecorp/items/ItemsApi.java",
      "line": 42,
      "tag": "business"
    },
    {
      "url": "https://api.telecorp.example/v1/items/",
      "file": "com/telecorp/items/ItemsApi.java",
      "line": 58,
      "tag": "business"
    }
  ],
  "secrets_redacted": 0
}
```

Reading `ItemsApi.java:42` and `:58` (the synthesis step above) shows a Retrofit interface:

```java
public interface ItemsApi {
    @GET("v1/items")
    Call<List<ItemDto>> listItems(@Query("page") int page);

    @GET("v1/items/{id}")
    Call<ItemDto> getItem(@Path("id") String id);
}
```

Note the `:58` literal was only the path *prefix* (`.../items/`); the `{id}` template comes
from the `@Path("id")` annotation at the call site, not from the raw URL literal — this is
the runtime-assembly point (Method, step 5) showing up in miniature.

Resulting `features/items/openapi.yaml` (excerpt):

```yaml
openapi: 3.0.3
info:
  title: telecorp items API (recovered)
  version: "0.1-recovered"
paths:
  /v1/items:
    get:
      operationId: listItems
      parameters:
        - name: page
          in: query
          required: false
          schema:
            type: integer
      responses:
        "200":
          description: List of items
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Item"
        default:
          description: "Error contract not statically observed — runtime, pending capture"
  /v1/items/{id}:
    get:
      operationId: getItem
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Single item
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Item"
components:
  schemas:
    Item:
      # fields below are 🟢 literal — from ItemDto.java, same file:line neighborhood
      type: object
      properties:
        id:
          type: string
        name:
          type: string
```

## Consumer — dev, via `openapi_generator`

The value is generation, not documentation: the dev runs `openapi_generator` (or an
equivalent Dart-targeted generator) against `features/<slice>/openapi.yaml` and gets
**Freezed DTOs + a Dio client** for free — typed request/response models and a client method
per operation, instead of hand-writing them from a Java read-through. This is the payoff
that justifies the Method steps above: every field recovered 🟢 becomes a typed field the
dev never types by hand; every field left ⬜ shows up as a visible gap in the generated
model (an open/untyped schema) instead of a silently wrong guess baked into a DTO.

## Honesty stamp — do not fabricate a WebView contract

A WebView-routed feature's `openapi.yaml` is **born ⬜/blind** — there is no endpoint slice
to synthesize from (Input, above), and the loop must not manufacture one just to fill the
file. The contract only starts to exist once the Fetch-tap actually runs against the
Flutter-hosted SPA (`../cognitive-sequence.md`, "The WebView branch"), and even then it is
gated by the same tamper/identity wall as the dynamic pass — the tap may see the client-side
call and still be refused the real backend response. Until the tap runs: do not write paths
inferred from the SPA's JS alone into `openapi.yaml` as if they were a confirmed contract —
either omit the file and mark the feature `blind` in the dossier, or write it with every path
stamped ⬜ and a note that it reflects JS reading, not a captured contract. The same
discipline applies to the native route's runtime-assembled bases (Method, step 5): a
plausible-looking path is not the same fact as an anchored one, and keeping that distinction
visible in the artifact — not just in the analyst's head — is this recipe's whole point.
