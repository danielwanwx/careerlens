# Quality gates

Before export, verify:

- required sections, enums, and Priority A/B/C semantics are valid;
- candidate claims use candidate-owned references;
- target research is never counted as candidate proof;
- resources include scope, skip guidance, completion check, freshness, and
  verification state, with duplicate URLs removed;
- volatile claims include source and freshness metadata;
- total planned minutes fit the declared capacity and horizon;
- missing critical inputs remain visible;
- no secret, local absolute path, raw private text, provider payload,
  unsupported metric, ownership claim, or fabricated first-person answer
  enters the artifact;
- any upstream score, readiness state, or interview gate remains unchanged.

Thin input should produce `decision_state.kind: input_gate`, no displayed
numeric score, ranked questions, and `quality.export_ready: false`.

