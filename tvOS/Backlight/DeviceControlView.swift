//
//  DeviceControlView.swift
//  Backlight
//
//  Created by Dan Appel on 4/17/21.
//

import SwiftUI
import ParticleSwift

struct DeviceControlView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var defaults: Defaults

    @State var brightness: Int? = 100

    var body: some View {
        Group {
            if let deviceInfo = deviceManager.detailedDeviceInformation, let brightness = brightness {
                VStack {
                    Text("Brightness").font(.title2)
                    Spacer()
                    BrightnessPickerView(increment: 5, bounds: 0..<100, brightness: brightness) { brightness in
                        self.brightness = brightness
                        self.deviceManager.setBrightness(brightness, deviceId: deviceInfo.deviceID)
                    }
                }
            } else {
                Spacer()
            }
        }
        .padding()
        .onReceive(deviceManager.$detailedDeviceInformation) { device in
            guard let device = device, self.verifyDevice(device: device) else {
                return
            }
            self.deviceManager.fetchBrightness(deviceId: device.deviceID)
        }
        .onReceive(deviceManager.$currentBrightness) { brightness in
            self.brightness = brightness
        }
    }

    private func verifyDevice(device: DeviceDetailInformation) -> Bool {
        if !device.functions.contains("setBrightness") {
            DispatchQueue.main.async {
                deviceManager.lastError = "Selected device is not supported by Backlight"
                defaults.deviceId = nil
            }
            return false
        }
        return true
    }
}
