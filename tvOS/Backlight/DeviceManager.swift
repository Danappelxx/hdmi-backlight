//
//  DeviceManager.swift
//  Backlight
//
//  Created by Dan Appel on 4/16/21.
//

import Foundation
import ParticleSwift

class DeviceManager {
    public static var auth: Authentication! {
        guard let path = Bundle.main.path(forResource: "keys", ofType: "json"),
              let data = try? Data(contentsOf: URL(fileURLWithPath: path)),
              let auth = try? JSONDecoder().decode(Authentication.self, from: data) else {
            return nil
        }
        return auth
    }
}

struct Authentication: Codable {
    var clientId: String
    var clientSecret: String
}

extension DeviceManager: SecureStorage {

    func username(_ realm: String) -> String? {
        nil
    }

    func password(_ realm: String) -> String? {
        nil
    }

    func oauthClientId(_ realm: String) -> String? {
        Self.auth.clientId
    }

    func oauthClientSecret(_ realm: String) -> String? {
        Self.auth.clientSecret
    }

    func oauthToken(_ realm: String) -> OAuthToken? {
        nil
    }

    func updateOAuthToken(_ token: OAuthToken?, forRealm realm: String) {
    }
}
