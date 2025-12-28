import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

Item {
    ColumnLayout {
        anchors.fill: parent
        // anchors.margins: 20
        // spacing: 20
        // Main Scrollable Content
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

                Label {
                    text: "Settings"
                    color: theme.textColor
                    font.bold: true
                    font.pixelSize: 32
                }

                // Appearance Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Label {
                        text: "Appearance"
                        font.bold: true
                        color: theme.textColor
                        font.pixelSize: 18
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
                }

                // Directory List Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Label {
                        text: "Add or remove directories Photobase should scan:"
                        font.bold: true
                        color: theme.textColor
                        font.pixelSize: 18
                    }
                    
                    // Container for List + Buttons
                    Rectangle {
                        Layout.fillWidth: true
                        height: 300 // Fixed height for the editor area as per typical usage, or could be flexible
                        color: theme.isDark ? "#1e1e1e" : "#f5f5f5" // Tinted background
                        border.color: theme.borderColor
                        radius: 4
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            ListView {
                                id: pathsList
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                model: settingsController.scanPaths
                                clip: true
                                
                                delegate: ItemDelegate {
                                    width: ListView.view.width
                                    text: modelData
                                    contentItem: Text {
                                        text: modelData
                                        color: theme.textColor
                                        elide: Text.ElideLeft
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    highlighted: ListView.isCurrentItem
                                    onClicked: pathsList.currentIndex = index
                                    background: Rectangle {
                                        color: highlighted ? theme.highlightColor : "transparent"
                                        opacity: highlighted ? 0.3 : 1.0
                                    }
                                }
                                
                                highlight: Rectangle {
                                    color: theme.highlightColor
                                    opacity: 0.2
                                }
                                highlightMoveDuration: 0
                            }
                            
                            // Buttons inside the container
                            RowLayout {
                                // Layout.alignment: Qt.AlignRight
                                
                                // Add button
                                Item {
                                    width: 20
                                    height: 20
                                    Layout.alignment: Qt.AlignBottom

                                    Image {
                                        id: addIcon
                                        source: "file:assets/icons/plus.svg" 
                                        sourceSize.width: 20
                                        sourceSize.height: 20
                                        visible: false
                                    }

                                    MultiEffect {
                                        id: addEffect
                                        source: addIcon
                                        anchors.fill: parent
                                        colorization: 1.0
                                        colorizationColor: theme.buttonTextColor
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            settingsController.addPath()
                                        }
                                    }
                                }

                                // Remove button
                                Item {
                                    width: 20
                                    height: 20
                                    Layout.alignment: Qt.AlignBottom

                                    Image {
                                        id: removeIcon
                                        source: "file:assets/icons/minus.svg" 
                                        sourceSize.width: 20
                                        sourceSize.height: 20
                                        visible: false
                                    }

                                    MultiEffect {
                                        id: removeEffect
                                        source: removeIcon
                                        anchors.fill: parent
                                        colorization: 1.0
                                        colorizationColor: theme.buttonTextColor
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (pathsList.currentIndex >= 0) {
                                                settingsController.removePath(pathsList.currentIndex)
                                            }
                                        }
                                    }
                                }
                                
                                // Spacer
                                Item {
                                    Layout.fillWidth: true
                                }

                                // Apply Changes button
                                Button {
                                    text: "Apply Changes"
                                    onClicked: settingsController.applyChanges()
                                }
                            }
                        }
                    }
                }

                Item {
                    implicitWidth: aboutRow.implicitWidth
                    implicitHeight: aboutRow.implicitHeight
                    
                    Layout.fillWidth: false 

                    // 2. The Layout handles the horizontal positioning
                    RowLayout {
                        id: aboutRow
                        anchors.fill: parent
                        spacing: 10
                        
                        Text {
                            text: "About Photobase"
                            color: theme.textColor
                            verticalAlignment: Text.AlignVCenter
                        }

                        // Link icon
                        Item {
                            width: 16
                            height: 16
                            Layout.alignment: Qt.AlignVCenter

                            Image {
                                id: linkIcon
                                source: "file:assets/icons/external-link-3px.svg"
                                sourceSize: Qt.size(16, 16)
                                visible: false
                            }

                            MultiEffect {
                                source: linkIcon
                                anchors.fill: parent
                                colorization: 1.0
                                colorizationColor: theme.textColor
                            }
                        }
                    }

                    // 3. The MouseArea fills the entire Item (Text + Icon)
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            aboutDialog.open()
                        }
                    }
                }

            }
        }
    }

    About {
        id: aboutDialog
    }
}