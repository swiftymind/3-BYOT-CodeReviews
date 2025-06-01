import Foundation

protocol GitHubServiceProtocol {
    func searchUser(username: String) async throws -> GitHubUser
}

enum NetworkError: Error, LocalizedError {
    case invalidURL
    case noData
    case userNotFound
    case invalidResponse
    case decodingError

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .noData:
            return "No data received"
        case .userNotFound:
            return "User not found"
        case .invalidResponse:
            return "Invalid response"
        case .decodingError:
            return "Failed to decode response"
        }
    }
}