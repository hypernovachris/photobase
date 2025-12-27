import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
                                Layout.alignment: Qt.AlignRight
                                
                                Button {
                                    text: "Add"
                                    onClicked: settingsController.addPath()
                                    // Basic styling if needed, or rely on Theme via palette in main? 
                                    // For now standard controls look okay, but let's apply partial palette if possible or leave default
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
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}