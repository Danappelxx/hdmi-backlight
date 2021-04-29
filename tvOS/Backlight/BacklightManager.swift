//
//  BacklightManager.swift
//  Backlight
//
//  Created by Dan Appel on 4/28/21.
//

import Foundation
import Combine

public struct Brightness: Codable {
    public var brightness: Int
}

public enum BacklightState: Int, Codable {
    case stopped = -1
    case none = 0
    case video = 1
    case audio = 2
    case error = 3
    case changingVideoToAudio = 4
    case changingAudioToVideo = 5
}

public struct BacklightStateRequest: Codable {
    public var state: BacklightState
}

public struct Response<T> {
    let value: T
    let response: URLResponse
}

public class BacklightManager {
    public static let shared = BacklightManager()

    private static let base = URL(string: "http://pi.local:80")!

    private func request<T: Codable>(_ request: URLRequest) -> AnyPublisher<Response<T>, Error> {
        return URLSession
            .shared
            .dataTaskPublisher(for: request)
            .tryMap { result -> Response<T> in
                let value = try JSONDecoder().decode(T.self, from: result.data)
                return Response(value: value, response: result.response)
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    private func request(_ request: URLRequest) -> AnyPublisher<Response<Void>, Error> {
        return URLSession
            .shared
            .dataTaskPublisher(for: request)
            .tryMap { result -> Response<Void> in
                return Response(value: (), response: result.response)
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    public func getBrightness() -> AnyPublisher<Response<Brightness>, Error> {

        let url = Self.base.appendingPathComponent("/brightness")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        return self.request(request)
    }

    public func setBrightness(_ brightness: Int) -> AnyPublisher<Response<Void>, Error> {

        let url = Self.base.appendingPathComponent("/brightness")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "content-type")

        do {
            request.httpBody = try JSONEncoder().encode(Brightness(brightness: brightness))
        } catch let error {
            return Fail(error: error)
                .eraseToAnyPublisher()
        }

        return self.request(request)
    }

    public func getState() -> AnyPublisher<Response<BacklightStateRequest>, Error> {

        let url = Self.base.appendingPathComponent("/state")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        return self.request(request)
    }

    public func setState(_ state: BacklightState) -> AnyPublisher<Response<Void>, Error> {

        let url = Self.base.appendingPathComponent("/state")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "content-type")

        do {
            request.httpBody = try JSONEncoder().encode(BacklightStateRequest(state: state))
        } catch let error {
            return Fail(error: error)
                .eraseToAnyPublisher()
        }

        return self.request(request)
    }
}
