import SwiftUI

enum AppearanceMode: String, CaseIterable, Identifiable {
    case dark, light, system

    var id: String { rawValue }

    var title: String {
        switch self {
        case .dark: "深色"
        case .light: "淺色"
        case .system: "系統"
        }
    }

    var colorScheme: ColorScheme? {
        switch self {
        case .dark: .dark
        case .light: .light
        case .system: nil
        }
    }
}

@main
struct ExchangeGuideApp: App {
    @StateObject private var store = DashboardStore()
    @AppStorage("appearanceMode") private var appearanceMode = AppearanceMode.light.rawValue

    var body: some Scene {
        WindowGroup {
            ExchangeRootView()
                .environmentObject(store)
                .preferredColorScheme(AppearanceMode(rawValue: appearanceMode)?.colorScheme)
                .tint(ExchangeColor.accent)
                .task { await store.load() }
        }
    }
}
