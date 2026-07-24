# Exchange Guide iOS HIG Screen Specification

Product type: a student-facing exchange application information app. Phase one supports Chang Gung University. The interface prioritizes finding eligible schools, deadlines, subsidies, official documents, application steps, and student experiences.

## Adaptive Navigation

### iPhone and compact width

- Use a native `TabView` with five persistent destinations: Home, Schools, Deadlines, Support, and Eligibility.
- Keep the tab bar visible while moving within each destination so students retain orientation.
- Do not show a sidebar on iPhone. Apple notes that sidebars consume too much space in compact environments.
- Put primary task controls in the lower portion of the home content and keep every target at least 44 x 44 pt.

### iPad and regular width

- Use `NavigationSplitView` with a 240 pt minimum, 280 pt ideal, and 340 pt maximum sidebar.
- Keep the current destination visibly selected and use the standard sidebar toggle and edge-swipe behavior.
- Show no more than two hierarchy levels in the sidebar.
- Allow the campus image in the detail column to extend beneath the floating sidebar using `backgroundExtensionEffect()` on iOS 26.

## Main Screen

1. **Navigation bar:** compact title, refresh action, native Liquid Glass supplied by the system.
2. **Campus identity:** real CGU campus image, 190 pt on compact width and 240 pt on regular width.
3. **Summary metrics:** three standard content cards for schools, schedules, and document summaries.
4. **Task controls:** four interactive Liquid Glass controls for the student's highest-frequency actions.
5. **Coverage chart:** a native Swift Charts horizontal bar chart for schools, schedules, documents, and official sources.
6. **Current information:** standard-material cards for the nearest application period and a featured partner university.

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
| Tab item | System controlled | System Liquid Glass | Preserves each section's navigation state | Five or fewer items; concise labels |
| Toolbar icon | Minimum 44 x 44 pt | System Liquid Glass | Native pressed, hover, focus, and disabled states | Explicit action label |
| Task control | Minimum 72 pt high | Interactive regular Liquid Glass | Touch and pointer response; subtle hover on iPad | Title and outcome hint combined |
| Primary action | Minimum 52 pt high | Prominent Liquid Glass on iOS 26 | Pressed, focused, disabled | Verb-first label; no color-only meaning |
| Metric card | Flexible width, minimum 88 pt high | Standard content surface | Read-only | Combined metric name and value |
| Information card | Full column width | Standard content surface | Navigation or disclosure | Heading, summary, and source relationship |
| Coverage chart | 164 pt high | Standard content surface | Read-only in MVP | Combined spoken summary of every value |

## Thumb Reach and Spacing

- Use the 8 pt spacing base. Compact margins are 16 pt; regular margins are 24 pt.
- Keep primary mobile task controls below the top identity and summary region.
- Avoid placing the only submission action solely in the top navigation bar.
- Use 44 pt as the minimum target for icon buttons, clear controls, links, pickers, and segmented controls.
- Maintain at least 8 pt between adjacent touch targets.

## Acceptance Checks

- VoiceOver announces the current sidebar destination and every chart value.
- Dynamic Type does not truncate destination names or primary task labels.
- The interface remains usable with Reduce Transparency, Increase Contrast, and Reduce Motion.
- iPhone portrait has no sidebar and no horizontal scrolling.
- iPad regular width keeps sidebar selection visible while detail content changes.
- Liquid Glass never obscures long application text, eligibility rules, or official document summaries.

## Apple References

- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines
- Materials and Liquid Glass: https://developer.apple.com/design/human-interface-guidelines/materials
- Sidebars: https://developer.apple.com/design/human-interface-guidelines/sidebars
- Split views: https://developer.apple.com/design/human-interface-guidelines/split-views
- Applying Liquid Glass to custom views: https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views
- Swift Charts: https://developer.apple.com/documentation/charts
