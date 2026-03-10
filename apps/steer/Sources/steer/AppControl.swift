import AppKit
import Foundation

enum AppControl {
    struct AppInfo: Codable {
        let name: String
        let pid: Int32
        let bundleId: String?
        let isActive: Bool
    }

    static func list() -> [AppInfo] {
        NSWorkspace.shared.runningApplications
            .filter { $0.activationPolicy == .regular }
            .map { AppInfo(
                name: $0.localizedName ?? "?",
                pid: $0.processIdentifier,
                bundleId: $0.bundleIdentifier,
                isActive: $0.isActive
            )}
    }

    static func find(_ name: String) -> NSRunningApplication? {
        let n = name.lowercased()
        return NSWorkspace.shared.runningApplications.first {
            $0.activationPolicy == .regular &&
            ($0.localizedName?.lowercased() == n || $0.bundleIdentifier?.lowercased() == n)
        }
    }

    static func activate(_ name: String) throws {
        guard let app = find(name) else { throw SteerError.appNotFound(name) }
        app.activate(options: .activateIgnoringOtherApps)
    }

    static func launch(_ name: String) throws {
        if !NSWorkspace.shared.launchApplication(name) {
            throw SteerError.appNotFound(name)
        }
    }

    static func hide(_ name: String) throws {
        guard let app = find(name) else { throw SteerError.appNotFound(name) }
        app.hide()
    }

    static func unhide(_ name: String) throws {
        guard let app = find(name) else { throw SteerError.appNotFound(name) }
        app.unhide()
        app.activate(options: .activateIgnoringOtherApps)
    }

    static func quit(_ name: String, force: Bool = false) throws {
        guard let app = find(name) else { throw SteerError.appNotFound(name) }
        let ok = force ? app.forceTerminate() : app.terminate()
        if !ok {
            throw SteerError.windowActionFailed(force ? "force-quit" : "quit", name)
        }
    }

    static func frontmost() -> NSRunningApplication? {
        NSWorkspace.shared.frontmostApplication
    }
}
