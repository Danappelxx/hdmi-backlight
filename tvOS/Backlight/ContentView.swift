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

    @Environment(\.resetFocus) var resetFocus
    @Namespace var namespace

    @State var alertError: String?

    var body: some View {
        NavigationView {
            if deviceManager.detailedDeviceInformation != nil {
                VStack {
                    DeviceControlView()
                    Spacer()
                    HStack {
                        Text("")
                            .frame(maxWidth: .infinity)
                            .prefersDefaultFocus(false, in: namespace)
                            .disabled(true)
                            .focusable()
                        NavigationLink(
                            destination: DevicePickerView(),
                            label: {
                                Image(systemName: "gear").font(.largeTitle)
                            }
                        )
                            .prefersDefaultFocus(in: namespace)
                    }
                }
            } else if defaults.deviceId != nil {
                ProgressView()
            } else {
                DevicePickerView()
            }
        }
        .focusScope(namespace)
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
        .onAppear {
            resetFocus(in: namespace)
        }
        .alert(item: self.$alertError) { error in
            Alert(title: Text(error))
        }
    }
}
