import Foundation

enum SteerError: LocalizedError {
    case captureFailure(String)
    case appNotFound(String)
    case elementNotFound(String)
    case noSnapshot
    case permissionDenied(String)
    case screenNotFound(Int, available: Int)
    case windowNotFound(String)
    case windowActionFailed(String, String)
    case clipboardEmpty(String)
    case waitTimeout(String, Double)
    case ocrFailed(String)
    case approvalNotFound(String)
    case approvalExpired(String)
    case approvalRevoked(String)
    case approvalExhausted(String)
    case approvalMismatch(expected: String, actual: String)

    var errorDescription: String? {
        switch self {
        case .captureFailure(let msg): return "Capture failed: \(msg)"
        case .appNotFound(let name): return "App not found: \(name)"
        case .elementNotFound(let q): return "Element not found: \(q)"
        case .noSnapshot: return "No snapshot. Run 'steer see' first."
        case .permissionDenied(let p): return "Permission denied: \(p). Grant in System Settings > Privacy & Security."
        case .screenNotFound(let idx, let avail): return "Screen \(idx) not found. \(avail) screen(s) available (use 0-\(avail - 1)). Run 'steer screens' to list."
        case .windowNotFound(let name): return "No window found for app: \(name)"
        case .windowActionFailed(let action, let name): return "Window \(action) failed for: \(name)"
        case .clipboardEmpty(let type): return "Clipboard has no \(type) content"
        case .waitTimeout(let cond, let sec): return "Timeout after \(Int(sec))s waiting for \(cond)"
        case .ocrFailed(let msg): return "OCR failed: \(msg)"
        case .approvalNotFound(let id): return "Approval not found: \(id)"
        case .approvalExpired(let id): return "Approval expired: \(id)"
        case .approvalRevoked(let id): return "Approval revoked: \(id)"
        case .approvalExhausted(let id): return "Approval already consumed: \(id)"
        case .approvalMismatch(let expected, let actual): return "Approval mismatch: expected \(expected), got \(actual)"
        }
    }
}
