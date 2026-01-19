import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    ColumnLayout {
        anchors.fill: parent
        // anchors.margins: 20
        // spacing: 20

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ColumnLayout {
                x: 20
                y: 20
                width: scrollView.availableWidth - 40
                spacing: 20

                // Label {
                //     text: "Places"
                //     color: theme.textColor
                //     font.bold: true
                //     font.pixelSize: 32
                // }

                Label {
                    text: "Coming soon..."
                    color: theme.textColor
                    Layout.alignment: Qt.AlignCenter
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
}
