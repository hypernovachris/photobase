import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10

        Label {
            text: "Add or remove directories Photobase should scan:"
            font.bold: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            ListView {
                id: pathsList
                model: settingsController.scanPaths
                clip: true
                
                delegate: ItemDelegate {
                    width: ListView.view.width
                    text: modelData
                    highlighted: ListView.isCurrentItem
                    onClicked: pathsList.currentIndex = index
                }
                
                highlight: Rectangle {
                    color: "lightgray"
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            
            Button {
                text: "Add"
                onClicked: settingsController.addPath()
            }
            
            Button {
                text: "Remove"
                enabled: pathsList.currentIndex >= 0
                onClicked: {
                    if (pathsList.currentIndex >= 0) {
                        settingsController.removePath(pathsList.currentIndex)
                    }
                }
            }

            Button {
                text: "Apply Changes"
                onClicked: settingsController.applyChanges()
            }
        }
    }
}
