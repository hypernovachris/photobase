import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: aboutDialog
    title: "Credits & Licenses"
    width: 400
    height: 500
    anchors.centerIn: parent
    modal: true
    standardButtons: Dialog.Close

    ColumnLayout {
        anchors.fill: parent
        spacing: 15

        // App Info Header
        Column {
            Layout.fillWidth: true
            spacing: 5
            
            Label {
                text: "Photobase"
                font.pixelSize: 22
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Label {
                text: "Version 0.0.0"
                font.pixelSize: 14
                color: "gray"
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        HorizontalHeaderView { Layout.fillWidth: true } // Visual separator

        // License Scroll Area
        ScrollView {
            id: licenseScrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: licenseScrollView.availableWidth
                spacing: 20

                // Lucide Icons Section
                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Lucide Icons"
                        font.bold: true
                    }
                    Label {
                        text: "Copyright © 2024 Lucide Contributors\n" +
                              "Licensed under the ISC License."
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Text {
                        text: "Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies."
                        font.pixelSize: 11
                        color: "#666"
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Qt Framework"
                        font.bold: true
                    }
                    Label {
                        text: "This application uses the Qt Framework under the LGPL v3 license."
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }
}