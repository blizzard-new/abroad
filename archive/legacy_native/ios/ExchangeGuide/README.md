# Exchange Guide iOS

Native SwiftUI client for the Chang Gung University exchange information API.

## Requirements

- macOS with Xcode 26+
- iOS 17+
- XcodeGen (`brew install xcodegen`)
- The FastAPI service from the project root

## Create and open the project

```bash
cd ios/ExchangeGuide
xcodegen generate
open ExchangeGuide.xcodeproj
```

The simulator default API is `http://127.0.0.1:8000`. For a physical iPhone, edit the `EXCHANGE_API_BASE_URL` launch environment variable to the Mac's LAN address, for example `http://192.168.1.20:8000`. Production/TestFlight builds must use HTTPS.

The app keeps iOS 17 as its deployment target. When built with Xcode 26, iOS 26 devices use native Liquid Glass (`glassEffect`, glass button styles, and background extension). iOS 17-25 use system-material fallbacks, and Reduce Transparency uses opaque semantic surfaces.

## Implemented flows

- Home task dashboard and official-data freshness
- Floating icon-first Liquid Glass dock on iPhone and iPad `NavigationSplitView` sidebar
- Native Swift Charts coverage visualization
- Searchable partner university list
- University snapshot rail, four-cell application summary, expandable restrictions, detailed workflow, and student experiences
- Deadline list
- Scholarship and official document summaries
- Basic eligibility check
- Dark, light, and system appearance modes
- Source-backed life information sorted by coverage, with concrete bullet points
- Community snapshot rail, four-cell post summaries, expandable bodies and comments, public chat, invitation-only private messages, reports, and blocks
- Light off-white glass dashboard with compact task tiles and an on-demand coverage chart
- Dynamic Type, VoiceOver labels, Reduce Motion, and minimum 44pt targets

The SwiftUI source is complete, but iOS builds still require macOS and Xcode; the Windows workspace cannot run the iOS compiler or Simulator.

The shared visual specification is `../../docs/design/apple-design-system.md`. The screen-level HIG handoff is `../../docs/design/ios-hig-screen-spec.md`.
