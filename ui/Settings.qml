import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10

        Label {
            text: "Appearance"
            font.bold: true
            color: theme.textColor
        }

        RowLayout {
            Label {
                text: "Theme:"
                color: theme.textColor
            }
            ComboBox {
                model: ["System", "Normal", "Dark"]
                currentIndex: model.indexOf(settingsController.theme)
                onActivated: (index) => {
                    settingsController.theme = model[index]
                }
                
                delegate: ItemDelegate {
                    width: parent.width
                    text: modelData
                    contentItem: Text {
                        text: modelData
                        color: theme.textColor
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        color: highlighted ? theme.highlightColor : theme.buttonColor
                    }
                    highlighted: ListView.isCurrentItem
                }
                
                contentItem: Text {
                    leftPadding: 10
                    rightPadding: 10
                    text: parent.displayText
                    color: theme.textColor
                    verticalAlignment: Text.AlignVCenter
                }
                
                background: Rectangle {
                    color: theme.buttonColor
                    border.color: theme.borderColor
                }
            }
        }

        Label {
            text: "Add or remove directories Photobase should scan:"
            font.bold: true
            color: theme.textColor
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
