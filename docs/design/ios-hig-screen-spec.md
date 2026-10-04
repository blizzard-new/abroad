# Exchange Guide iOS HIG Screen Specification

Product type: a student-facing exchange application information app. Phase one supports Chang Gung University. The interface prioritizes finding eligible schools, deadlines, subsidies, official documents, application steps, and student experiences.

## Adaptive Navigation

### iPhone and compact width

- Keep a native `TabView` for destination state, hide its system bar, and overlay a five-control floating Liquid Glass dock.
- Use the same visual order on iOS and Android: Home circle, Deadlines circle, elongated Search/Schools capsule, Support/Documents circle with a compact update badge, and Profile/Eligibility circle.
- Keep the tab bar visible while moving within each destination so students retain orientation.
- Do not show a sidebar on iPhone. Apple notes that sidebars consume too much space in compact environments.
- Show visible text only in the center Search capsule. Every icon-only control keeps a localized accessibility label and selected state.
- Keep every destination target at least 44 x 44 pt and above the home indicator.

### iPad and regular width

- Use `NavigationSplitView` with a 240 pt minimum, 280 pt ideal, and 340 pt maximum sidebar.
- Keep the current destination visibly selected and use the standard sidebar toggle and edge-swipe behavior.
- Show no more than two hierarchy levels in the sidebar.
- Allow the campus image in the detail column to extend beneath the floating sidebar using `backgroundExtensionEffect()` on iOS 26.

## Main Screen

1. **Navigation bar:** compact title, refresh action, native Liquid Glass supplied by the system.
2. **Campus identity:** real CGU campus image, 150 pt on compact width and 190 pt on regular width.
3. **Task controls:** a two-column icon-first grid on compact width and four columns on regular width; visible copy is limited to one short title.
4. **Current information:** the nearest application period uses an inline disclosure; a featured partner university opens a separate detail screen.
5. **Coverage chart:** a collapsed disclosure that reveals the native Swift Charts summary only on demand.

## Material Rules

- Liquid Glass is limited to navigation, toolbars, tab bars, sidebars, and important custom controls.
- Content cards use opaque semantic surfaces or standard material. They do not use Liquid Glass.
- iOS 26 uses native `glassEffect`, `.glassProminent`, and `backgroundExtensionEffect` APIs.
- iOS 17-25 use `ultraThinMaterial` and semantic separators as a compatibility fallback.
- Reduce Transparency replaces glass with an opaque semantic surface and a 1 pt separator.
- Reduce Motion removes custom scale animations. System transitions remain under platform control.

## Component Specifications

| Component | Size | Material | Interaction | Accessibility |
| --- | --- | --- | --- | --- |
| Sidebar row | Minimum 52 pt high | System sidebar | Persistent selected state | SF Symbol plus visible label; selected value announced |
| Floating dock item | 54 x 54 pt circles; 110 x 54 pt center capsule | Native Liquid Glass or material fallback | Preserves each section's navigation state | Icon-only items have explicit labels; selected value announced |
| Toolbar icon | Minimum 44 x 44 pt | System Liquid Glass | Native pressed, hover, focus, and disabled states | Explicit action label |
| Task control | Minimum 116 pt high | Interactive regular Liquid Glass | Touch and pointer response; subtle hover on iPad | Short visible title; outcome kept as accessibility hint |
| Primary action | Minimum 52 pt high | Prominent Liquid Glass on iOS 26 | Pressed, focused, disabled | Verb-first label; no color-only meaning |
| Metric card | Flexible width, minimum 88 pt high | Standard content surface | Read-only | Combined metric name and value |
| Snapshot rail | 108–148 pt per fact, 52 pt dividers | Standard content surface | Horizontal drag on compact width | Each fact combines the short label and value |
| Information summary grid | 112 pt minimum per cell; 2 x 2 compact, one row regular | Standard content surface | Read-only or whole-card navigation | Icon is decorative; label and value are combined |
| Information card | Full column width | Standard content surface | Navigation or disclosure | Heading, summary, and source relationship |
| Coverage chart | Collapsed by default | Standard content surface | Disclosure expands the chart | Combined spoken summary of every value |

## Thumb Reach and Spacing

- Use the 8 pt spacing base. Compact margins are 16 pt; regular margins are 24 pt.
- Keep primary mobile task controls below the top identity and summary region.
- Avoid placing the only submission action solely in the top navigation bar.
- Use 44 pt as the minimum target for icon buttons, clear controls, links, pickers, and segmented controls.
- Maintain 6–8 pt between adjacent dock targets and at least 8 pt elsewhere.
- Reserve the four-cell summary for short comparable facts. Put long conditions, deadlines, post bodies, comments, and source notes in disclosures or reading views.

## Acceptance Checks

- VoiceOver announces the current sidebar destination and every chart value.
- Dynamic Type does not truncate the Search label or primary task labels; icon-only destinations remain fully named to VoiceOver.
- The interface remains usable with Reduce Transparency, Increase Contrast, and Reduce Motion.
- iPhone portrait has no sidebar and no horizontal scrolling.
- iPad regular width keeps sidebar selection visible while detail content changes.
- Liquid Glass never obscures long application text, eligibility rules, or official document summaries.
- Android and iOS compact layouts preserve the same dock order, icon meaning, short labels, disclosure behavior, and destination structure.

## Apple References

- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines
- Materials and Liquid Glass: https://developer.apple.com/design/human-interface-guidelines/materials
- Sidebars: https://developer.apple.com/design/human-interface-guidelines/sidebars
- Split views: https://developer.apple.com/design/human-interface-guidelines/split-views
- Applying Liquid Glass to custom views: https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views
- Swift Charts: https://developer.apple.com/documentation/charts
