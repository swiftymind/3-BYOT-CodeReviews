import Foundation

final class GitHubService: GitHubServiceProtocol {
    private let session: URLSession
    private let baseURL = "https://api.github.com"

    init(session: URLSession = .shared) {
        self.session = session
    }

    func searchUser(username: String) async throws -> GitHubUser {
        guard let url = URL(string: "\(baseURL)/users/\(username)") else {
            throw NetworkError.invalidURL
        }

        do {
            let (data, response) = try await session.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.invalidResponse
            }

            switch httpResponse.statusCode {
            case 200:
                break
            case 404:
                throw NetworkError.userNotFound
            default:
                throw NetworkError.invalidResponse
            }

            guard !data.isEmpty else {
                throw NetworkError.noData
            }

            do {
                let user = try JSONDecoder().decode(GitHubUser.self, from: data)
                return user
            } catch {
                throw NetworkError.decodingError
            }
        } catch let error as NetworkError {
            throw error
        } catch {
            throw NetworkError.invalidResponse
        }
    }
}