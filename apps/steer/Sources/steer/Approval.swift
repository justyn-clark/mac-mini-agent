import Foundation

struct ApprovalContractRecord: Codable {
    let approval_id: String
    let action: String
    let target: String
    let created_at: Int
    let expires_at: Int?
    let revoked_at: Int?
    let max_uses: Int?
    let uses: Int
    let metadata: [String: String]?
}

enum ApprovalControl {
    static var approvalDir: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".mac-mini-agent")
            .appendingPathComponent("approvals")
    }

    static func load(_ approvalId: String) throws -> ApprovalContractRecord {
        let path = approvalDir.appendingPathComponent("\(approvalId).json")
        guard FileManager.default.fileExists(atPath: path.path) else {
            throw SteerError.approvalNotFound(approvalId)
        }
        let data = try Data(contentsOf: path)
        return try JSONDecoder().decode(ApprovalContractRecord.self, from: data)
    }

    static func validate(_ approvalId: String, action: String, target: String) throws {
        let record = try load(approvalId)
        let now = Int(Date().timeIntervalSince1970)

        if let revokedAt = record.revoked_at, revokedAt > 0 {
            throw SteerError.approvalRevoked(approvalId)
        }
        if let expiresAt = record.expires_at, now > expiresAt {
            throw SteerError.approvalExpired(approvalId)
        }
        if let maxUses = record.max_uses, record.uses >= maxUses {
            throw SteerError.approvalExhausted(approvalId)
        }
        if record.action != action {
            throw SteerError.approvalMismatch(expected: record.action, actual: action)
        }
        if record.target != target {
            throw SteerError.approvalMismatch(expected: record.target, actual: target)
        }
    }
}
