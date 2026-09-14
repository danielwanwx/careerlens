# `personalized_runbook.v1`

The canonical JSON artifact contains:

`identity`, `input_status`, `target_picture`, `candidate_picture`,
`fit_assessment`, `decision_state`, `resume_guidance`, `target_portfolio`,
`strategy`, `module_selection`, `selection_methodology`, `interview_map`, `learning_tracks`, `question_bank`,
`answer_guidance`, `roadmap`, `application_experiment`, `sources`, and
`quality`. `delta` is optional during refresh.

Every action also has an inspectable `artifact` and `exit_gate`. Priority A must
link to a target requirement, diagnosis gap, or interview dimension.

Every resource has an HTTPS URL, source class, linked dimension, why it fits,
reading scope, skip guidance, completion condition, sequence, dependencies,
freshness, verification state, candidate starting state, resource role,
assigned output, estimated time, and mapped questions.

Every question records its selection reason, priority, confidence, mapped
requirements, mapped rounds, and objective completion standard.

The runbook may project an accepted upstream diagnosis. It must not recompute
readiness, unlock interviews, or manufacture candidate evidence.
