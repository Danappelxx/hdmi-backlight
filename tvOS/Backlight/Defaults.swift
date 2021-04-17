//
//  Defaults.swift
//  Backlight
//
//  Created by Dan Appel on 4/17/21.
//

import Foundation
import Combine

public class Defaults: ObservableObject {
    public static let shared = Defaults()

    @Published public var deviceId: String? {
        didSet {
            UserDefaults.standard.set(deviceId, forKey: "device_id")
        }
        willSet {
            self.objectWillChange.send()
        }
    }

    private init() {
        self.deviceId = UserDefaults.standard.string(forKey: "device_id")
    }
}
