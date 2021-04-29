//
//  ContentView.swift
//  Backlight
//
//  Created by Dan Appel on 4/16/21.
//

import SwiftUI

struct ContentView: View {

    @EnvironmentObject var defaults: Defaults

    var body: some View {
        BacklightManagerView()
    }
}
