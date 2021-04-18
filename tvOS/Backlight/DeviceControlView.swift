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

    @State var selectedBrightness: Int = 100 {
        didSet {
            if selectedBrightness > 100 {
                selectedBrightness = 100
            }
        }
    }
    @State var disablePlus: Bool = true
    @State var disableMinus: Bool = false

    var brightnessText: String {
        var str = ""
        for char in String(self.selectedBrightness) {
            if char == "5" {
                str.append("biz")
            } else {
                str.append(char)
            }
        }
        return str
    }

    var body: some View {
        Group {
            if deviceManager.detailedDeviceInformation != nil {
                VStack {
                    Text("Brightness").font(.title2)
                    Spacer()
                        Button(action: {
                            selectedBrightness += 5
                            updateBrightness()
                        }, label: {
                            Text("+").font(.largeTitle).bold()
                            // Image(systemName: "plus.rectangle").font(.largeTitle)
                        }).disabled(self.disablePlus)

                        Text("\(brightnessText)").font(.title)

                        Button(action: {
                            selectedBrightness -= 5
                            updateBrightness()
                        }, label: {
                            Text("-").font(.largeTitle).bold()
                            // Image(systemName: "minus.rectangle").font(.largeTitle)
                        }).disabled(self.disableMinus)
                }
            } else {
                Spacer()
            }
        }
        .padding()
        .onReceive(deviceManager.$detailedDeviceInformation) { device in
            guard let device = device else {
                return
            }
            self.verifyDevice(device: device)
        }
    }

    private func verifyDevice(device: DeviceDetailInformation) {
        if !device.functions.contains("setBrightness") {
            DispatchQueue.main.async {
                deviceManager.lastError = "Selected device is not supported by Backlight"
                defaults.deviceId = nil
            }
        }
    }

    private func updateBrightness() {
        self.disablePlus = self.selectedBrightness >= 100
        self.disableMinus = self.selectedBrightness <= 0

        deviceManager.setBrightness(self.selectedBrightness, deviceId: deviceManager.detailedDeviceInformation!.deviceID)
    }
}
