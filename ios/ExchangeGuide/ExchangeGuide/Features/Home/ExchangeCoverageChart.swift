import Charts
import SwiftUI

private struct CoveragePoint: Identifiable {
    let id: String
    let label: String
    let value: Int
    let color: Color
}

struct ExchangeCoverageChart: View {
    let dashboard: StudentDashboard

    private var points: [CoveragePoint] {
        [
            CoveragePoint(
                id: "schools",
                label: "合作校",
                value: dashboard.partnerUniversities.count,
                color: ExchangeColor.chartBlue
            ),
            CoveragePoint(
                id: "deadlines",
                label: "時程",
                value: dashboard.applicationPeriods.count,
                color: ExchangeColor.chartPeach
            ),
            CoveragePoint(
                id: "documents",
                label: "文件",
                value: dashboard.documentExplanations.count,
                color: ExchangeColor.chartLavender
            ),
            CoveragePoint(
                id: "sources",
                label: "來源",
                value: dashboard.sources.count,
                color: ExchangeColor.chartMint
            )
        ]
    }

    var body: some View {
        VStack(alignment: .leading, spacing: ExchangeSpacing.md) {
            ExchangeSectionHeader(title: "整理進度")

            HStack(spacing: ExchangeSpacing.lg) {
                ZStack {
                    Chart(points) { point in
                        SectorMark(
                            angle: .value("數量", max(point.value, 1)),
                            innerRadius: .ratio(0.7),
                            angularInset: 2.5
                        )
                        .cornerRadius(8)
                        .foregroundStyle(point.color)
                    }
                    VStack(spacing: 2) {
                        Text("\(points.reduce(0) { $0 + $1.value })")
                            .font(.system(.title, design: .rounded).weight(.bold))
                            .foregroundStyle(ExchangeColor.labelPrimary)
                            .contentTransition(.numericText())
                        Text("筆重點")
                            .font(ExchangeTypography.caption)
                            .foregroundStyle(ExchangeColor.labelSecondary)
                    }
                }
                .frame(width: 154, height: 154)

                VStack(alignment: .leading, spacing: ExchangeSpacing.sm) {
                    ForEach(points) { point in
                        HStack(spacing: ExchangeSpacing.xs) {
                            Circle().fill(point.color).frame(width: 10, height: 10)
                            Text(point.label)
                                .font(ExchangeTypography.subheadline)
                            Spacer(minLength: 4)
                            Text("\(point.value)")
                                .font(ExchangeTypography.headline)
                        }
                    }
                }
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(
                "資料整理進度：合作校 \(dashboard.partnerUniversities.count) 所，時程 \(dashboard.applicationPeriods.count) 筆，文件 \(dashboard.documentExplanations.count) 份，來源 \(dashboard.sources.count) 筆"
            )
        }
        .exchangeCard()
    }
}
