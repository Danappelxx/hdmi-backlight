//
//  BrightnessPickerView.swift
//  Backlight
//
//  Created by Dan Appel on 4/18/21.
//

import SwiftUI

struct BrightnessPickerView: View {

    @Environment(\.resetFocus) var resetFocus
    @Namespace var namespace

    enum StepDirection {
        case incr
        case decr
    }

    let increment: Int
    let bounds: Range<Int>

    @State var brightness: Int
    var action: ((Int) -> ())?

    @State private var disablePlus: Bool = false
    @State private var disableMinus: Bool = false

    var brightnessText: String {
        var str = ""
        for char in String(self.brightness) {
            if char == "5" {
                str.append("biz")
            } else {
                str.append(char)
            }
        }
        return str
    }

    var body: some View {
        VStack {
            Button(action: {
                updateBrightness(direction: .incr)
            }, label: {
                Text("+").font(.largeTitle).bold()
            }).disabled(self.disablePlus).prefersDefaultFocus(!disablePlus, in: namespace)

            Text("\(brightnessText)").font(.title)

            Button(action: {
                updateBrightness(direction: .decr)
            }, label: {
                Text("-").font(.largeTitle).bold()
            }).disabled(self.disableMinus).prefersDefaultFocus(!disableMinus, in: namespace)
        }
            .focusScope(namespace)
            .onAppear {
                self.disablePlus = self.brightness >= bounds.upperBound
                self.disableMinus = self.brightness <= bounds.lowerBound
                resetFocus(in: namespace)
            }
    }

    private func updateBrightness(direction: StepDirection) {

        var newBrightness = brightness

        switch direction {
        case .incr: newBrightness += increment
        case .decr: newBrightness -= increment
        }

        disablePlus = newBrightness >= bounds.upperBound
        disableMinus = newBrightness <= bounds.lowerBound

        if disablePlus {
            newBrightness = bounds.upperBound
        }
        if disableMinus {
            newBrightness = bounds.lowerBound
        }

        brightness = newBrightness

        action?(brightness)
    }
}
