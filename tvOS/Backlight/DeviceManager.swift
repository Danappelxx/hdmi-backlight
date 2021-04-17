//
//  DeviceManager.swift
//  Backlight
//
//  Created by Dan Appel on 4/16/21.
//

import Foundation
import ParticleSwift

public class DeviceManager: ObservableObject {
    @Published public var devices: [DeviceInformation] = []
    @Published public var detailedDeviceInformation: DeviceDetailInformation? = nil {
        willSet {
            // in case this is externally set to nil
            self.objectWillChange.send()
        }
    }
    @Published public var lastError: String? = nil

    public static let shared = DeviceManager()

    private var particle: ParticleCloud
    // need to keep this reference around
    private var authenticationManager: ParticleAuthenticationManager

    public init() {
        let authenticationManager = ParticleAuthenticationManager()
        self.particle = ParticleCloud(secureStorage: authenticationManager)
        self.authenticationManager = authenticationManager
    }

    public func fetchDevices() {
        self.particle.devices { devices in
            DispatchQueue.main.async {
                switch devices {
                case .success(let devices):
                    self.devices = devices
                case .failure(let error):
                    self.lastError = "\(error)"
                }
            }
        }
    }

    public func fetchDetailedDeviceInformation(device: DeviceInformation) {
        self.fetchDetailedDeviceInformation(deviceId: device.deviceID)
    }

    public func fetchDetailedDeviceInformation(deviceId: String) {
        self.particle.deviceDetailInformation(deviceId) { deviceInfo in
            DispatchQueue.main.async {
                switch deviceInfo {
                case .success(let deviceInfo):
                    print("updated detailed device information")
                    self.detailedDeviceInformation = deviceInfo
                case .failure(let error):
                    self.lastError = "\(error)"
                }
            }
        }
    }

    public func setBrightness(_ value: Int, deviceId: String) {
        self.particle.callFunction("setBrightness", deviceID: deviceId, argument: String(value)) { result in
            print("setBrightness result: \(result)")
        }
    }
}

struct Authentication: Codable {
    var clientId: String
    var clientSecret: String
    var username: String
    var password: String
}

private class ParticleAuthenticationManager: SecureStorage {
    private lazy var auth: Authentication! = {
        guard let path = Bundle.main.path(forResource: "keys", ofType: "json"),
              let data = try? Data(contentsOf: URL(fileURLWithPath: path)),
              let auth = try? JSONDecoder().decode(Authentication.self, from: data) else {
            return nil
        }
        return auth
    }()

    var token: OAuthToken?

    func username(_ realm: String) -> String? {
        self.auth.username
    }

    func password(_ realm: String) -> String? {
        self.auth.password
    }

    func oauthClientId(_ realm: String) -> String? {
        self.auth.clientId
    }

    func oauthClientSecret(_ realm: String) -> String? {
        self.auth.clientSecret
    }

    func oauthToken(_ realm: String) -> OAuthToken? {
        self.token
    }

    func updateOAuthToken(_ token: OAuthToken?, forRealm realm: String) {
        self.token = token
    }
}
