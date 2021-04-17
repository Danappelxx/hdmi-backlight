//
//  DevicePickerView.swift
//  Backlight
//
//  Created by Dan Appel on 4/17/21.
//

import SwiftUI

struct DevicePickerView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var defaults: Defaults
    @Environment(\.presentationMode) var presentationMode: Binding<PresentationMode>

    var body: some View {
        VStack {
            Text("Pick a device to control")
                .padding()
            List(deviceManager.devices) { device in
                Button(device.name) {
                    defaults.deviceId = device.deviceID
                    self.presentationMode.wrappedValue.dismiss()
                }
            }.padding()
        }
        .onAppear {
            self.deviceManager.fetchDevices()
        }
    }
}
