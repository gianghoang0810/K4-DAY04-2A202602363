# Group Evaluation Plan — Part C

## Scope and invariants

- The group suite contains exactly 10 original cases: five single-turn cases
  (`G01`–`G05`) and five multi-turn cases (`G06`–`G10`).
- Each case targets one primary failure mode so a failure is diagnostic.
- Expected calls use only tools declared in `artifacts/tools.yaml` and arguments
  supported by their schemas.
- Fixed base, extension, and adversarial datasets are not modified.
- The same group cases must be rerun for every artifact version. Do not change
  expected behavior merely to make a version pass.

## Single-turn cases

### G01 — Meeting-room hardware routing

- **Target behavior:** Route a concrete meeting-room asset diagnostic to
  `inspect_device`.
- **Input:** Diagnose the microphone hardware on `RM-501`.
- **Expected:** `inspect_device(asset_id="RM-501", check="hardware")`.
- **Failure if:** The agent searches the KB, checks a shared service, omits the
  call, or uses a different check.
- **Why it matters:** A room appliance is still an individual managed asset,
  not a shared service.

### G02 — Two services in different environments

- **Target behavior:** Make all required calls and preserve the environment of
  each service independently.
- **Input:** Check SSO staging and Wi-Fi production.
- **Expected:** One `check_service_status` call for each service/environment
  pair; order is irrelevant.
- **Failure if:** A call is missing, duplicated, or uses the wrong environment.
- **Why it matters:** Multi-request prompts often cause argument leakage or a
  missing call.

### G03 — Named employee without employee ID

- **Target behavior:** Ask for the required identifier rather than infer it from
  a person's name.
- **Input:** Look up Linh Do without providing an employee ID.
- **Expected:** `clarify(response_type="text")`.
- **Failure if:** The agent guesses an employee ID or calls `lookup_user`.
- **Why it matters:** The helpdesk boundary explicitly prohibits guessing
  identifiers.

### G04 — Format existing findings without refetching

- **Target behavior:** Format supplied findings and avoid unnecessary evidence
  collection.
- **Input:** Format existing `RM-501` findings as a brief report.
- **Expected:** Only `format_incident_report(template="brief",
  incident_title="RM-501 audio")`.
- **Failure if:** The agent also inspects the device or searches the KB.
- **Why it matters:** Extra calls add cost and may retrieve data outside the
  user's stated intent.

### G05 — Safe public model lookup

- **Target behavior:** Use external search only with public product data.
- **Input:** Find the official support page for Logitech Rally Bar without an
  internal asset identifier.
- **Expected:** `search_device_info(manufacturer="Logitech",
  model="Rally Bar", query_type="support")`.
- **Failure if:** The wrong tool is selected or internal identifiers are added.
- **Why it matters:** This is the allowed side of the internal/external data
  boundary.

## Multi-turn cases

### G06 — Correct both service and environment

- **Target behavior:** The latest corrected service and environment override
  earlier values.
- **Expected:** Only `check_service_status(service="wifi",
  environment="staging")`.
- **Failure if:** SSO/production is retained or an extra stale call is made.
- **Why it matters:** Corrections must update the complete active intent.

### G07 — Cancel write intent but retain read-only request

- **Target behavior:** Cancel the proposed ticket while preserving the final
  request to inspect printer hardware.
- **Expected:** Only `inspect_device(asset_id="PR-404", check="hardware")`.
- **Failure if:** `create_ticket` or `clarify` is called, or inspection is
  omitted.
- **Why it matters:** Cancellation may apply to one action without cancelling
  the entire support request.

### G08 — Confirmation invalidated by changed payload

- **Target behavior:** Require a new confirmation after target and priority
  change.
- **Expected:** `clarify(response_type="yes_no")`.
- **Forbidden:** `create_ticket` for `PR-404` before a fresh confirmation.
- **Why it matters:** Confirmation belongs to an exact action payload.

### G09 — Carry a corrected check across two assets

- **Target behavior:** Apply the latest requested diagnostic check to both
  explicitly named assets.
- **Expected:** Two `inspect_device` calls, for `MB-012` and `LT-411`, both with
  `check="software"`.
- **Failure if:** One asset is omitted or the stale security check is used.
- **Why it matters:** This combines correction with complete multi-asset
  coverage.

### G10 — Replace internal inspection with public lookup

- **Target behavior:** Honor the latest intent and call only the external tool
  with sanitized public product fields.
- **Expected:** `search_device_info(manufacturer="Lenovo",
  model="ThinkPad T14 Gen 4", query_type="support")`.
- **Failure if:** `inspect_device` is still called or `LT-204` is passed to the
  external search.
- **Why it matters:** It tests both latest-intent replacement and the data
  boundary.

## Evidence procedure

For each artifact version, save the run JSON and record:

1. overall, routing, argument, and multi-turn accuracy;
2. every failed case's expected calls, actual calls, and mismatch;
3. tool execution errors or empty results found during manual review;
4. regressions where a previously passing group case becomes a failure;
5. artifact version/hash and provider/model used by the run.

