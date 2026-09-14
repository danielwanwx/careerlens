# Example Studio Data Platform Resume Variant

## Objective

Create an employer-specific recruiter-facing resume derived from the current canonical Data Platform resume while preserving the canonical resume unchanged.

## Content Change

- Remove only the `Self-Service ML Deployment` bullet from the `Declarative Data Orchestration Platform` subsection.
- Preserve all other wording, dates, metrics, links, section ordering, typography, spacing, and page structure.

## Source and Output

- Source: the latest editable Data Platform resume in the configured private
  application-materials directory.
- Output: a separate PDF named `Candidate_Resume.pdf` under an employer-specific
  private application directory.
- Do not overwrite the canonical application-ready resume.

## Verification

- Confirm the removed bullet is absent from extracted text.
- Confirm no unrelated content changed.
- Render both PDF pages and visually inspect for gaps, overflow, clipping, or accidental pagination changes.
- Present the PDF to the candidate for review before replacing an uploaded
  application attachment.

## Browser Handoff

After candidate approval, remove the current application attachment and upload
the reviewed employer-specific PDF. Do not submit the application until all
remaining application questions have been reviewed under Pilot policy.
