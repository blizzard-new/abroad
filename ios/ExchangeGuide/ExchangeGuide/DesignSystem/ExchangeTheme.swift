import SwiftUI
import UIKit

enum ExchangeColor {
    static let backgroundPrimary = dynamic(light: 0xFBF9F4, dark: 0x080A0D)
    static let backgroundSecondary = dynamic(light: 0xFFFFFF, dark: 0x0F1217)
    static let backgroundTertiary = dynamic(light: 0xF3F1EA, dark: 0x171B22)
    static let backgroundSelected = dynamic(light: 0xE9EEFA, dark: 0x102C3B)
    static let labelPrimary = dynamic(light: 0x1C1C1E, dark: 0xF5F7FA)
    static let labelSecondary = dynamic(light: 0x6B7280, dark: 0xA7AFBB)
    static let labelTertiary = dynamic(light: 0x9CA3AF, dark: 0x747E8B)
    static let separator = dynamic(light: 0xE8E5DC, dark: 0x2A3039)
    static let accent = dynamic(light: 0x4E74C9, dark: 0x8AB0F5)
    static let success = dynamic(light: 0x3E8E63, dark: 0x5FC98F)
    static let warning = dynamic(light: 0xA36B2E, dark: 0xE8B36B)
    static let danger = dynamic(light: 0xC94F4F, dark: 0xF08080)
    static let indigo = dynamic(light: 0x6D68B8, dark: 0xA9A4E8)

    static let successBackground = dynamic(light: 0xE8F3EC, dark: 0x102419)
    static let warningBackground = dynamic(light: 0xF9F0E1, dark: 0x2A1D0C)
    static let dangerBackground = dynamic(light: 0xF9E9E9, dark: 0x2B1415)
    static let infoBackground = dynamic(light: 0xEBF0FA, dark: 0x102330)

    static let chartBlue = dynamic(light: 0xA8C5F0, dark: 0x6E96D8)
    static let chartPeach = dynamic(light: 0xF2C9A2, dark: 0xD9A26B)
    static let chartLavender = dynamic(light: 0xC7C2EE, dark: 0x928BD9)
    static let chartMint = dynamic(light: 0xAADCC3, dark: 0x6FBF97)

    private static func dynamic(light: UInt32, dark: UInt32) -> Color {
        Color(uiColor: UIColor { traits in
            UIColor(hex: traits.userInterfaceStyle == .dark ? dark : light)
        })
    }
}

extension UIColor {
    convenience init(hex: UInt32, alpha: CGFloat = 1) {
        self.init(
            red: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255,
            alpha: alpha
        )
    }
}

enum ExchangeSpacing {
    static let xxs: CGFloat = 4
    static let xs: CGFloat = 8
    static let sm: CGFloat = 12
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
    static let xxl: CGFloat = 40
    static let section: CGFloat = 48
}

enum ExchangeRadius {
    static let control: CGFloat = 12
    static let card: CGFloat = 22
    static let sheet: CGFloat = 24
}

enum ExchangeLayout {
    static let minimumTarget: CGFloat = 44
    static let fieldHeight: CGFloat = 48
    static let primaryButtonHeight: CGFloat = 52
    static let compactMargin: CGFloat = 16
    static let regularMargin: CGFloat = 24
    static let readableWidth: CGFloat = 680
}

enum ExchangeTypography {
    static let largeTitle = Font.largeTitle.weight(.bold)
    static let title = Font.title.weight(.bold)
    static let title2 = Font.title2.weight(.bold)
    static let title3 = Font.title3.weight(.semibold)
    static let headline = Font.headline.weight(.semibold)
    static let body = Font.body
    static let callout = Font.callout.weight(.medium)
    static let subheadline = Font.subheadline.weight(.medium)
    static let footnote = Font.footnote.weight(.medium)
    static let caption = Font.caption.weight(.semibold)
}

struct ExchangeCardModifier: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        content
            .padding(20)
            .background(.regularMaterial)
            .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.card, style: .continuous))
            .shadow(
                color: .black.opacity(colorScheme == .dark ? 0.28 : 0.05),
                radius: 14,
                y: 6
            )
    }
}

struct ExchangeGlassControlModifier: ViewModifier {
    let interactive: Bool
    let tint: Color?
    let cornerRadius: CGFloat

    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency

    @ViewBuilder
    func body(content: Content) -> some View {
        if reduceTransparency {
            content
                .background(ExchangeColor.backgroundSecondary)
                .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                        .stroke(ExchangeColor.separator, lineWidth: 1)
                }
        } else if #available(iOS 26.0, *) {
            content.glassEffect(
                .regular.tint(tint).interactive(interactive),
                in: .rect(cornerRadius: cornerRadius)
            )
        } else {
            content
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                        .stroke(ExchangeColor.separator.opacity(0.45), lineWidth: 1)
                }
        }
    }
}

extension View {
    func exchangeCard() -> some View {
        modifier(ExchangeCardModifier())
    }

    func exchangePageBackground() -> some View {
        background(
            ExchangeColor.backgroundPrimary
                .overlay(
                    LinearGradient(
                        colors: [
                            ExchangeColor.chartBlue.opacity(0.10),
                            .clear,
                            ExchangeColor.chartPeach.opacity(0.08)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .ignoresSafeArea()
        )
    }

    func exchangeGlassControl(
        interactive: Bool = false,
        tint: Color? = nil,
        cornerRadius: CGFloat = ExchangeRadius.control
    ) -> some View {
        modifier(
            ExchangeGlassControlModifier(
                interactive: interactive,
                tint: tint,
                cornerRadius: cornerRadius
            )
        )
    }

    @ViewBuilder
    func exchangeProminentButtonStyle() -> some View {
        if #available(iOS 26.0, *) {
            buttonStyle(.glassProminent)
        } else {
            buttonStyle(ExchangePrimaryButtonStyle())
        }
    }

    @ViewBuilder
    func exchangeBackgroundExtension() -> some View {
        if #available(iOS 26.0, *) {
            backgroundExtensionEffect()
        } else {
            self
        }
    }
}

struct ExchangePrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(ExchangeTypography.headline)
            .frame(maxWidth: .infinity, minHeight: ExchangeLayout.primaryButtonHeight)
            .foregroundStyle(Color(uiColor: UIColor(hex: 0x061018)))
            .background(backgroundColor(isPressed: configuration.isPressed))
            .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous))
            .opacity(isEnabled ? 1 : 0.45)
            .scaleEffect(configuration.isPressed && isEnabled ? 0.98 : 1)
            .animation(reduceMotion ? nil : .easeOut(duration: 0.09), value: configuration.isPressed)
    }

    private func backgroundColor(isPressed: Bool) -> Color {
        if !isEnabled { return ExchangeColor.backgroundTertiary }
        return isPressed ? ExchangeColor.accent.opacity(0.78) : ExchangeColor.accent
    }
}

struct ExchangeSecondaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(ExchangeTypography.headline)
            .frame(minHeight: ExchangeLayout.minimumTarget)
            .padding(.horizontal, ExchangeSpacing.md)
            .foregroundStyle(ExchangeColor.labelPrimary)
            .background(configuration.isPressed ? ExchangeColor.backgroundSelected : ExchangeColor.backgroundTertiary)
            .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous)
                    .stroke(ExchangeColor.separator, lineWidth: 1)
            }
            .opacity(isEnabled ? 1 : 0.45)
            .scaleEffect(configuration.isPressed && isEnabled ? 0.98 : 1)
            .animation(reduceMotion ? nil : .easeOut(duration: 0.09), value: configuration.isPressed)
    }
}

struct ExchangeIconButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(width: ExchangeLayout.minimumTarget, height: ExchangeLayout.minimumTarget)
            .foregroundStyle(ExchangeColor.labelPrimary)
            .background(configuration.isPressed ? ExchangeColor.backgroundSelected : ExchangeColor.backgroundTertiary)
            .clipShape(RoundedRectangle(cornerRadius: ExchangeRadius.control, style: .continuous))
            .opacity(isEnabled ? 1 : 0.45)
            .scaleEffect(configuration.isPressed && isEnabled ? 0.96 : 1)
            .animation(reduceMotion ? nil : .easeOut(duration: 0.09), value: configuration.isPressed)
    }
}
