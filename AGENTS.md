# Repository Instructions

## Authoritative documents

- `docs/implementation-plan.md`
- `docs/requirements.md`
- `docs/status.md`
- `docs/decision-log.md`

## Mandatory plan alignment

Before implementation, review all authoritative documents and report:

- current `PLAN_VERSION`
- current phase
- requirement IDs addressed by the request
- allowed changes
- prohibited changes
- any conflict between the request and the approved plan

Do not replace or recreate the implementation plan. Use `PROPOSED_CHANGE` only when changing `CAREER-SYSTEMS-V1` or the approved `AI-LEARNING-V1.0` plan. Present the plan difference, reason, impact, and alternatives, and wait for explicit approval before changing the plan or implementing the change.

## Scope and safety

- The initial implementation uses deterministic fake embedding and answer-generation providers only.
- Do not add the OpenAI SDK, request or store an API key, or call an external AI, embedding, video, or subtitle API.
- Do not add features, dependencies, or architecture outside the approved plan.
- Do not push, create a pull request, deploy, or enable automatic CI triggers unless explicitly requested.
- Preserve user changes and unrelated worktree changes.
- Keep requirements, implementation, tests, status, and decisions synchronized.
- Backend authorization is authoritative; frontend visibility checks are not security boundaries.
- Never treat generated content as a fixed correct answer. Preserve evidence, refusal decisions, and evaluation results.
- Never mark a requirement complete while its acceptance criteria are unverified.

## Initial exclusions

Do not implement learning progress, completion tracking, bookmarks, quizzes, upload services, CDN integration, external video delivery, billing, background queue products, multilingual support, production monitoring, production deployment, automatic improvement, or automatic prompt/threshold rewriting.

## Quiz mode

When conducting a code-reading quiz:

- inspect current code before each question
- ask one question at a time
- do not reveal answers or target files before the user's answer
- preserve the user's answer verbatim
- distinguish repository-specific facts from standards, framework behavior, conventions, and alternatives
- update only `docs/code-reading-quiz-progress.md` if that file is later approved for creation
