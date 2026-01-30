import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import "components"

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
            contentHeight: settingsContent.height + 40

            ColumnLayout {
                id: settingsContent
                x: theme.paddingMedium
                y: theme.paddingMedium
                width: scrollView.availableWidth - (theme.paddingMedium * 2)
                spacing: theme.spacingLarge

                // Appearance Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: theme.spacingMedium
                    Header {
                        text: "Appearance"
                    }

                    ColumnLayout {
                        BodyText {
                            text: "Choose a color scheme for Photobase to use"
                        }
                        ComboBox {
                            id: control
                            model: ["System", "Normal", "Dark"]
                            currentIndex: model.indexOf(settingsController.theme)
                            onActivated: (index) => {
                                settingsController.theme = model[index]
                            }
                        }
                    }
                }

                // Directory List Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: theme.spacingMedium

                    Header {
                        text: "Gallery"
                    }
                    
                    BodyText {
                        text: "Add or remove directories Photobase should scan"
                    }
                    
                    // Container for List + Buttons
                    Rectangle {
                        Layout.fillWidth: true
                        height: 300 // Fixed height for the editor area as per typical usage, or could be flexible
                        color: theme.secondaryBackgroundColor
                        border.color: theme.borderColor
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.spacingMedium
                            spacing: theme.spacingMedium
                            
                            ListView {
                                id: pathsList
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                model: settingsController.scanPaths
                                clip: true
                                
                                delegate: ItemDelegate {
                                    width: ListView.view.width
                                    text: modelData
                                    contentItem: BodyText {
                                        text: modelData
                                        elide: Text.ElideLeft
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    highlighted: ListView.isCurrentItem
                                    onClicked: pathsList.currentIndex = index
                                    background: Rectangle {
                                        color: highlighted ? theme.secondaryHighlightColor : "transparent"
                                    }
                                }
                                
                                highlight: Rectangle {
                                    color: theme.secondaryHighlightColor
                                }
                                highlightMoveDuration: 0
                            }
                            
                            // Buttons inside the container
                            RowLayout {
                                // Layout.alignment: Qt.AlignRight
                                
                                // Add button
                                IconButton {
                                    width: 20
                                    height: 20
                                    Layout.alignment: Qt.AlignBottom
                                    source: "file:assets/icons/plus.svg"
                                    color: theme.textColor
                                    onClicked: settingsController.addPath()
                                }

                                // Remove button
                                IconButton {
                                    width: 20
                                    height: 20
                                    Layout.alignment: Qt.AlignBottom
                                    source: "file:assets/icons/minus.svg"
                                    color: theme.textColor
                                    onClicked: {
                                        if (pathsList.currentIndex >= 0) {
                                            settingsController.removePath(pathsList.currentIndex)
                                        }
                                    }
                                }
                                
                                // Spacer
                                Item {
                                    Layout.fillWidth: true
                                }

                                // Apply Changes button
                                StandardButton {
                                    text: "Apply Changes"
                                    onClicked: settingsController.applyChanges()
                                }
                            }
                        }
                    }
                }

                // About Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Header {
                        text: "About"
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
                            
                            BodyText {
                                text: "About Photobase"
                                verticalAlignment: Text.AlignVCenter
                            }

                            // Link icon
                            Item {
                                width: 16
                                height: 16
                                Layout.alignment: Qt.AlignVCenter

                                IconButton {
                                    clickable: false
                                    source: "file:assets/icons/external-link-3px.svg"
                                    iconSize: 16
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
    }

    About {
        id: aboutDialog
    }
}