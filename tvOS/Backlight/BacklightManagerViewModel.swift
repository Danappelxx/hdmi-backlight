//
//  BacklightManagerViewModel.swift
//  Backlight
//
//  Created by Dan Appel on 4/28/21.
//

import Combine

class BacklightManagerViewModel: ObservableObject {
    @Published var state: BacklightState? = nil
    @Published var brightness: Int? = nil
    @Published var error: Error? = nil

    var cancellationTokens: Set<AnyCancellable> = []

    init() {
        refresh()
    }

    func refresh() {
        let cancelGetBrightness = BacklightManager.shared.getBrightness()
            .sink(
                receiveCompletion: { completion in
                    guard case let .failure(error) = completion else {
                        return
                    }
                    self.error = error
                },
                receiveValue: { response in
                    self.brightness = response.value.brightness
                })

        let cancelGetState = BacklightManager.shared.getState()
            .sink(
                receiveCompletion: { completion in
                    guard case let .failure(error) = completion else {
                        return
                    }
                    self.error = error
                },
                receiveValue: { response in
                    self.state = response.value.state
                })

        self.cancellationTokens = [cancelGetBrightness, cancelGetState]
    }

    func setState(_ state: BacklightState) {
        let cancelSetState = BacklightManager.shared.setState(state)
            .sink(
                receiveCompletion: { completion in
                    guard case let .failure(error) = completion else {
                        return
                    }
                    self.error = error
                },
                receiveValue: { response in
                    self.refresh()
                })
        self.cancellationTokens = [cancelSetState]
    }

    func setBrightness(_ brightness: Int) {
        let cancelSetBrightness = BacklightManager.shared.setBrightness(brightness)
            .sink(
                receiveCompletion: { completion in
                    guard case let .failure(error) = completion else {
                        return
                    }
                    self.error = error
                },
                receiveValue: { response in
                    self.refresh()
                })
        self.cancellationTokens = [cancelSetBrightness]
    }
}
