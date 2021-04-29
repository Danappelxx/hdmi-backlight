//
//  BacklightManagerView.swift
//  Backlight
//
//  Created by Dan Appel on 4/28/21.
//

import SwiftUI

struct BacklightManagerView: View {
    @ObservedObject var viewModel = BacklightManagerViewModel()

    var errorBinding: Binding<String?> {
        Binding(
            get: {
                return viewModel.error?.localizedDescription
            },
            set: { newValue in
                if newValue == nil {
                    viewModel.error = nil
                }
            }
        )
    }

    var body: some View {
        if let brightness = viewModel.brightness, let state = viewModel.state {

            VStack {

                Text(String("State"))
                    .font(.headline)

                HStack {

                    Button(
                        action: {
                            self.viewModel.setState(.video)
                        },
                        label: {
                            if state == .video {
                                Text("Video")
                                    .underline()
                            } else {
                                Text("Video")
                            }
                        }
                    )

                    Button(
                        action: {
                            self.viewModel.setState(.audio)
                        },
                        label: {
                            if state == .audio {
                                Text("Audio")
                                    .underline()
                            } else {
                                Text("Audio")
                            }
                        }
                    )
                }

                Divider()
                    .padding()

                Text("Brightness")
                    .font(.headline)
                BrightnessPickerView(increment: 5, bounds: 0..<255, brightness: brightness) { newValue in
                    self.viewModel.setBrightness(newValue)
                }

            }
                .sheet(item: self.errorBinding) { error in
                    Text("Error: \(error)")
                    Button("Try again") {
                        self.viewModel.error = nil
                        self.viewModel.refresh()
                    }
                }

        } else {
            if let error = viewModel.error {
                Text("Error: \(error.localizedDescription)")
                Button("Try again") {
                    self.viewModel.error = nil
                    self.viewModel.refresh()
                }
            } else {
                ProgressView()
            }
        }
    }
}
