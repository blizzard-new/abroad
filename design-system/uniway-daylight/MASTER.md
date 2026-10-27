# UniWay Daylight — mobile design system

## Student goal

Help an exchange student decide where to go, know the next preparation task,
and get useful answers from other students. The home screen prioritizes the next
action and real saved deadlines. Empty accounts never receive invented progress,
deadlines, recommendations or community activity.

## Direction and references

Requested skill: [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md).
Read SKILL.md, references/pro-rules.md and quick-reference priorities 1–3.

Searches run with the skill's Python script:

- `student travel planning light --design-system`: travel palette relevant, but
  children's typography and animated Aurora direction did not fit this app.
- Narrowed once to `education dashboard minimal --design-system`: accepted the
  functional, spacious, high-contrast Minimalism guidance. The suggested landing
  page structure, gold palette and code font were not applied to a Chinese native app.
- `accessible navigation forms --stack flutter`: no results. Retried once with
  `accessibility --stack flutter`: matched Semantics, screen readers and TextScaler.

Product decisions below are adapted design choices, not verbatim generated results.
No external font dependency; use platform fonts for Traditional Chinese.

References viewed on 2026-10-25:

- [IDP Live official app page](https://www.idp.com/idp-live-app/?lang=en): inspected
  its app screenshots, light surfaces, separate community entry and application
  progress display. Borrow the clarity of task hierarchy, not brand graphics.
- [Erasmus+ App](https://hello.erasmusapp.eu/): its mobility journey/checklist and
  peer support inform UniWay's preparation routes and forum entry.

## Tokens

| Role | Color |
|---|---|
| Canvas | `#F6F8F7` |
| Surface | `#FFFFFF` |
| Main text | `#172D37` |
| Supporting text | `#52656E` |
| Primary | `#006C67` → `#075C64`, white label |
| Preparation / documents | `#315DA8` on `#EAF0FC` |
| Journey | `#006C67` on `#E2F3EE` |
| Budget / countdown | `#AC4934` on `#FCEEE7` |
| Form border | `#81938E` |
| Card separator | `#DCE5E3` |

Spacing: 4/8/12/16/20/24/32. Body 16; supporting copy 14; section 20–24;
home headline 28. Cards radius 24; inputs/buttons 16; floating navigation 30.
White cards are opaque, without per-card background blur. Glass is restricted to
navigation and primary controls; high contrast/reduced motion uses opaque surfaces.
The app intentionally uses this light theme even when the OS prefers dark mode.

## Components and behavior

- One dominant CTA per section; secondary actions use plain text or outline.
- Material vector icons, primarily outlined. Icon-only tabs retain tooltip,
  screen-reader name, selected state and at least 48 dp targets. No visible tab labels.
- Travel illustration is original vector code and excluded from semantics.
- School photos come only from existing verified image metadata. Loading/missing
  images keep their dimensions and show a neutral campus illustration.
- School cards are lazily built, including paired rows on wide layouts.
- Keep visible form labels, required markers and legal/qualification details.
  Errors remain near the submission control and failed forum drafts are retained.
- Root content maximum width 840; deeper forms use the existing narrower readable
  width. Preserve SafeArea and scroll padding behind floating navigation.
- Native widgets share the light palette. Keep provider/kind identifiers unchanged
  so existing installed widgets continue reading their account-scoped snapshots.

## Validation boundary

Automated tests cover phone/tablet/landscape at 2× text, reduced motion, theme
contrast, navigation, form submission failures, filters, account synchronization,
notifications and widget logout clearing. Emulator screenshots supplement tests.
Do not claim a human TalkBack/VoiceOver audit or physical iPhone testing.
No university data verification is part of this redesign.
