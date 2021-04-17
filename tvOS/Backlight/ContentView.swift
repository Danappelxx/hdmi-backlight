//
//  ContentView.swift
//  Backlight
//
//  Created by Dan Appel on 4/16/21.
//

import SwiftUI
import ParticleSwift

struct ContentView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var defaults: Defaults

    @State var alertError: String?

    var body: some View {
        NavigationView {
            if deviceManager.detailedDeviceInformation != nil {
                VStack {
                    DeviceControlView()
                    Spacer()
                    HStack {
                        Spacer()
                        NavigationLink(
                            destination: DevicePickerView(),
                            label: {
                                Image(systemName: "gear").font(.largeTitle)
                            }
                        )
                    }
                }
            } else if defaults.deviceId != nil {
                ProgressView()
            } else {
                DevicePickerView()
            }
        }
        .onReceive(self.deviceManager.$lastError) { error in
            self.alertError = error
        }
        .onReceive(self.defaults.$deviceId) { deviceId in
            guard let deviceId = deviceId else {
                self.deviceManager.detailedDeviceInformation = nil
                return
            }
            self.deviceManager.fetchDetailedDeviceInformation(deviceId: deviceId)
        }
        .alert(item: self.$alertError) { error in
            Alert(title: Text(error))
        }
    }
}
