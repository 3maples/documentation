# Voice Input — "Talk to Maple" (Mobile-First)

**Status:** Phases 1–4 complete — backend `/agents/transcribe`, portal capture plumbing `useVoiceInput`, composer mic UI + auto-send countdown, and FAB long-press ("hold to talk"); all tested and feature-flagged (`VOICE_INPUT_ENABLED` / `VITE_VOICE_INPUT_ENABLED`), uncommitted. Remaining: manual on-device pass (iPhone Safari + Android Chrome via HTTPS tunnel), then commit + rollout.
**Date:** 2026-07-04
**Decisions confirmed with Simon:** Hybrid STT · Auto-send with undo · Mic button + long-press FAB

## Context

The portal has **no voice input at all** today. On a phone, a landscaper must tap the green Maple FAB, tap the textarea, use the phone keyboard (or its built-in dictation), then tap Send — 3–4 taps plus typing, cumbersome with gloves at a job site. The goal is: **one gesture → speak → Maple acts.**

Job sites are noisy and crews may speak Spanish, so transcription quality matters. The backend's translation sandwich already accepts any language at `/agents/orchestrate`, so transcription should return text in the original spoken language and let the existing pipeline handle translation.

## UX Summary

- **Mic button in the Maple composer** (mobile + desktop): tap → pulsing red mic + elapsed timer + live interim words (or a level meter where SpeechRecognition is unavailable) → tap Stop → "Transcribing…" → transcript fills the input → **"Sending in 3… Tap to edit · Cancel"** countdown → auto-sends via the existing submit path.
- **Long-press (~500 ms) the floating Maple FAB** → panel opens already recording. One gesture from anywhere in the app. Normal tap keeps current behavior; `title="Hold to talk to Maple"`.
- 60 s max recording cap. Empty transcript → friendly "I didn't catch that" state, never an error toast. Panel close mid-recording cancels.

## Feature flag (added after Phase 2)

Dual-gated rollout, off by default on both sides:

- **Backend:** `VOICE_INPUT_ENABLED` (`config.py: voice_input_enabled`, default false). While off, `POST /agents/transcribe` returns 404 (not 403 — the flag's existence isn't advertised).
- **Portal:** `VITE_VOICE_INPUT_ENABLED` read by `src/lib/voiceInputFlag.ts` (same shape as `supportPanelFlag.ts`). `useVoiceInput.isSupported` is false while off, so any voice UI built in Phases 3–4 hides automatically.
- Both documented in the respective `.env.example` files. Enable both in dev to test; enable in prod when launching. Note the portal flag is build-time (Vite), so prod enablement means a rebuild/deploy.

## Architecture

**Hybrid STT:**
- **Authoritative path:** `MediaRecorder` records audio (`audio/webm;codecs=opus` on Chrome, `audio/mp4` on Safari) → `POST /agents/transcribe` → OpenAI `gpt-4o-mini-transcribe` (best word-error rate in noise, cheap ~$0.003/min) → `{text, language, duration_seconds}`.
- **Feedback path:** `webkitSpeechRecognition` interim results shown live while speaking — display only, never sent, all its errors swallowed (iOS-flaky by design). Fallback: `AnalyserNode` level meter.

## Backend (platform/)

- **NEW `services/transcription.py`** — validation (content-type allowlist with `;codecs` normalization, 20 MB cap, empty reject), cached raw `AsyncOpenAI` client (pattern: `services/work_item_summary.py`), `transcribe_audio()` wrapping OpenAI errors into `TranscriptionUpstreamError`.
- **`config.py`** — `transcription_model: str = Field(default="gpt-4o-mini-transcribe", validation_alias="OPENAI_MODEL_TRANSCRIPTION")` (matches existing model-config pattern).
- **`services/request_protection.py`** — `LLM_TRANSCRIBE_RATE_LIMIT = 20`/min per company (mirrors orchestrate's limiter).
- **`routers/agents.py`** — thin `POST /agents/transcribe` endpoint: same auth deps as orchestrate (`verify_verified_firebase_token` + `require_authenticated_user`), rate limit, size gate on `audio.size` before buffering (pattern: `routers/support.py`), 400 bad input / 429 rate / 502 clean upstream-failure message. Sets `set_llm_context(feature="transcribe")` for attribution; token-quota gating deliberately skipped (orchestrate enforces it seconds later).
- **NEW `tests/test_agents_transcribe_api.py`** (TDD first): happy path with mocked client, codecs-suffix accepted, bad type / empty / oversize → 400, upstream failure → 502, rate limit → 429, unit tests for validators.

## Frontend (portal/)

- **NEW `src/types/speech-recognition.d.ts`** — ambient `SpeechRecognition` / `webkitSpeechRecognition` types.
- **NEW `src/lib/voiceRecording.ts`** — pure helpers: `pickRecordingMimeType`, `extensionForMimeType`, `formatElapsed`, `mapGetUserMediaError`, error copy, `MAX_RECORDING_MS = 60_000`, `AUTO_SEND_DELAY_MS = 3_000`.
- **`src/api/agents.ts`** — `transcribe(blob, filename)` via FormData (`apiRequest` already handles FormData + auth headers).
- **NEW `src/components/Layout/useVoiceInput.ts`** — state machine `idle → requesting-permission → recording → transcribing → idle/error`; `getUserMedia` + `MediaRecorder` lifecycle, `AudioContext.resume()` immediately (iOS), optional SpeechRecognition interim feed, elapsed timer + max-duration auto-stop, `startRecording/stopRecording/cancelRecording`, full unmount cleanup.
- **`src/components/Layout/AiPanel.tsx`** — one hook instance (composer + FAB both live here; **zero changes to PortalLayout.tsx or useMapleAgent.ts**):
  - Composer: mic button beside Send (hidden if unsupported), recording overlay over the textarea (pulse, timer, interim text or 5-bar meter), transcribing spinner, inline dismissible error line.
  - Auto-send: transcript → `onAiInputChange(text)` + 3 s countdown strip; touching the textarea or Cancel aborts and leaves the text for manual review; countdown checks `isAiSubmitting` (double-submit backstop).
  - FAB: `onPointerDown` 500 ms timer, >10 px move cancels, fired-guard suppresses the click, `onContextMenu` preventDefault + `WebkitTouchCallout: none`; sets `autoRecordOnOpenRef` → `onToggleAiPanel()`; effect starts recording once open. Close-while-recording → cancel.
- **NEW tests** (vitest, `portal/tests/`): `voiceRecording.test.ts` (pure helpers), `useVoiceInput.test.tsx` (FakeMediaRecorder, stubbed getUserMedia/AudioContext, fake timers), `AiPanelVoice.test.tsx` (mic states, auto-send countdown, FAB long-press vs tap).

## Phasing (each committable, TDD within each)

1. Backend `/agents/transcribe` (platform repo) — tests + service + config + router; mypy/ruff/pytest green.
2. Voice capture plumbing (portal) — types, lib, API client, `useVoiceInput` + tests. No UI yet.
3. Composer mic UI + auto-send/undo (portal).
4. FAB long-press (portal) + manual device pass on iOS Safari + Android Chrome.

## Risks / Edge Cases

- iOS: `AudioContext` may start suspended from a timer callback — `resume()` in the pointer flow; worst case the meter is flat but recording works. Verify on-device in Phase 4.
- OpenAI SDK infers audio format from filename — always send `voice.webm`/`voice.mp4` matching the recorder mimeType; normalize `;codecs=` server-side.
- HTTPS required for `getUserMedia`: localhost is fine; LAN-IP phone testing needs a tunnel/HTTPS.
- Silence auto-stop (VAD) deliberately **deferred** — mowers/blowers read as speech; manual stop + 60 s cap covers v1.

## Explicitly deferred

TTS (Maple speaking back) · PWA/offline capture · VAD silence detection · hold-to-record push-to-talk on the mic button · transcription token metering/billing (attribution context is set) · language hint param (orchestrate handles any language).

## Verification

- Backend: `./run_tests.sh tests/test_agents_transcribe_api.py`, `./run_mypy.sh routers/agents.py services/transcription.py`, `./run_ruff.sh`.
- Portal: `npm test -- voiceRecording useVoiceInput AiPanelVoice`, `npm run typecheck`, `npm run lint`.
- Manual: Chrome desktop (mic in composer), then real devices — iPhone Safari + Android Chrome via HTTPS tunnel: tap-mic flow, long-press FAB flow, Spanish utterance end-to-end (transcribe → orchestrate translation sandwich → Spanish reply).
