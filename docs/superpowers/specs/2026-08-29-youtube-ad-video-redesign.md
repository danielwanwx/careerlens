# CareerLens YouTube Ad Video Redesign

Date: 2026-08-29  
Status: revised design, pending final review

## Objective

Turn the current 59-second product explainer into a clear YouTube-style ad for
job seekers. The video begins with a real candidate anxiety, uses ordinary
spoken language, and shows only enough product proof to make the promise
credible.

## Audience Problem

The viewer has found a job they want but cannot tell whether their resume is
strong enough, what the interviewer will challenge, or what to prepare first.
The video must make that situation recognizable in the first five seconds.

## Language Rules

- Use plain conversational English.
- Do not use em dashes or en dashes.
- Do not use slogan-like fragments such as “Evidence before advice.”
- Do not use abstract product language such as “evidence contract,” “decision
  boundary,” “auditable reasoning,” or “capacity-aware preparation.”
- Address the viewer directly with `you`.
- Prefer familiar verbs: find, check, show, pick, read, skip, practice, fix.
- Each sentence must sound natural when spoken aloud.

## On-Screen Text Rules

- Every spoken sentence appears on screen as designed kinetic subtitles.
- Break narration into short phrase groups rather than one static sentence.
- Use horizontal phrase bands, word replacement, masked reveals, and keyword
  scale changes so the typography carries the rhythm of the voice.
- Keep one readable phrase group at a time. Earlier words may remain as large
  background context only when they do not compete with the active phrase.
- Main text must remain readable on a phone-sized video player.
- Supporting text is optional and limited to one short line.
- Remove dates, commit hashes, source IDs, technical receipts, and provenance
  copy from the video.
- Remove decorative tags and dense explanatory cards.
- Do not place paragraphs inside product screenshots.
- Keep only numbers that communicate immediate value: selected questions,
  selected resources, planned hours, and available hours.
- Source detail remains in the interactive Runbook, not the advertisement.

## Story Structure

### Scene 1: Desired job

On-screen: `Found a job you really want?`

Purpose: establish a familiar moment without introducing CareerLens.

### Scene 2: Anxiety

On-screen: `But you are not sure your resume is strong enough.`

Purpose: name the actual worry.

### Scene 3: Compare

On-screen: `CareerLens checks your resume against the actual role.`

Visual: one resume, one job description, one simple comparison motion. No
source metadata or tags.

### Scene 4: Interview risk

On-screen: `See what you have and what they may ask about.`

Visual: a small number of large evidence states. No definitions or explanatory
paragraphs.

### Scene 5: Personalized Runbook

On-screen: `Get the questions you should practice.`

Visual: use the real generated Runbook, not a generic recreation. Reframe the
interface into camera-ready crops so the viewer can recognize the navigation,
the candidate-specific question, and the selection rationale without reading
the full desktop page. Move between Overview, Questions, Resources, and Plan.

### Scene 6: Learning and plan

On-screen sequence:

1. `Know what to read.`
2. `Know what to skip.`
3. `Follow a plan you can finish.`

Visual: continue through the real Runbook. Show one customized resource crop,
then the 27-hour preparation plan inside the 48-hour limit. Finish by checking
one plan task and showing a brief sun emoji completion response.

### Scene 7: Close

On-screen: `Know what to fix before you apply.`

Supporting line: `CareerLens is open source.`

Visual: product name and repository URL only. Remove terminal typing, commit
information, validation receipts, and secondary slogans.

## Narration Draft

```text
Found a job you really want?

But you are not sure if your resume is strong enough.

CareerLens checks your resume against the actual role. It shows what you
already have and what the interviewer may challenge.

Then it picks the questions you should practice. It tells you what to read,
what to skip, and why each resource is worth your time.

You get a plan that fits the time you actually have.

Know what to fix before you apply.
```

The final narration may change for timing, but it must preserve this plain
spoken tone and meaning.

## Motion and Composition

- Use large type and one focal object at a time, but change the pose within each
  sentence so scenes do not feel like static slides.
- Divide subtitle phrases into their own moving bands. Alternate left-to-right
  sweeps, masked word reveals, scale punches, and phrase stacking. Do not reuse
  the same entrance for consecutive lines.
- Highlight only the word currently carrying meaning. Hold the completed phrase
  long enough to read before it exits or becomes background context.
- Transition from kinetic type into the matching product crop using shared
  direction and scale, so the typography appears to lead into the interface.
- Treat the Runbook as a real product demonstration. Use camera crops, pans,
  punch-ins, nav selection changes, question expansion, resource focus, plan
  progress, and a task completion state.
- Keep the real interface content and design language, but enlarge and reframe
  the relevant region for video. Do not shrink the full desktop page into the
  frame.
- Avoid assembling many small cards simultaneously.
- Motion must support the spoken sentence rather than add independent
  information.
- Preserve reduced-motion-safe, deterministic rendering.

## Narration and Timeline Contract

- Use the final ElevenLabs audio as the source of truth for duration.
- Map each spoken phrase to an explicit start and end time in the transcript
  data. Scene boundaries must follow the audio rather than approximate equal
  sections.
- Each phrase becomes visible no later than its first audible word and remains
  readable through its final audible word.
- Product actions occur on the verb they illustrate: compare on `checks`, open
  Questions on `questions`, focus a resource on `read`, dismiss secondary
  material on `skip`, and check a plan task on `plan`.
- Silence and breath gaps are reserved for transitions. No caption should
  appear to speak before the voice.

## Real Runbook Demo Sequence

1. Overview crop shows the conditional recommendation and the four core
   outputs.
2. Navigation moves to Questions and opens one candidate-specific question.
3. Navigation moves to Resources and isolates the assigned scope, skip guidance,
   and completion condition for one resource.
4. Navigation moves to Plan and shows `27h` planned inside `48h` available.
5. One task is checked. Progress updates and a sun emoji appears briefly as the
   completion response.

The sequence is an authored demonstration of the existing generated artifact.
It must not imply that the page contains features or data that are absent from
the real Runbook.

## Audio

- Continue using the selected deep ElevenLabs voice.
- Regenerate narration after the script is finalized.
- Keep narration conversational, with short pauses after the first two
  questions.
- No background music is required unless it improves clarity without competing
  with speech.

## Acceptance Criteria

- No dates, commit hashes, receipts, or technical source identifiers appear.
- No em dash or en dash appears in on-screen copy or narration.
- No scene contains a paragraph of small text.
- Every scene has one immediately readable message.
- Every narrated phrase is represented on screen and aligned to the real audio.
- Consecutive subtitle beats use varied but coherent motion rather than one
  repeated entrance.
- The first five seconds clearly describe the viewer's job-search anxiety.
- The real generated Runbook is the main product proof and visibly demonstrates
  Overview, Questions, Resources, and Plan.
- The product sequence includes one authentic task completion interaction and a
  brief sun emoji response.
- The video still communicates question selection, customized learning, and a
  finite plan.
- HyperFrames runtime, layout, motion, and contrast checks pass.
- Final rendering waits for user approval of the refreshed preview.
