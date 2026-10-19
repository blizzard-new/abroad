import Foundation

@MainActor
final class DashboardStore: ObservableObject {
    @Published private(set) var dashboard: StudentDashboard?
    @Published private(set) var isLoading = false
    @Published private(set) var errorMessage: String?
    @Published private(set) var lastLoadedAt: Date?

    private let api: ExchangeAPIClient

    init(api: ExchangeAPIClient = .shared) {
        self.api = api
    }

    func load(force: Bool = false) async {
        if isLoading { return }
        if dashboard != nil && !force { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            dashboard = try await api.dashboard()
            lastLoadedAt = Date()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
