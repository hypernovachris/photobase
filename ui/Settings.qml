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
                x: 20
                y: 20
                width: scrollView.availableWidth - 40
                spacing: 20

                // Appearance Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Label {
                        text: "Appearance"
                        color: theme.textColor
                        font.pixelSize: 20
                    }

                    ColumnLayout {
                        Label {
                            text: "Choose a color scheme for Photobase to use"
                            color: theme.textColor
                            font.pixelSize: 14
                        }
                        ComboBox {
                            id: control
                            model: ["System", "Normal", "Dark"]
                            currentIndex: model.indexOf(settingsController.theme)
                            onActivated: (index) => {
                                settingsController.theme = model[index]
                            }

                            indicator: Item {
                                x: control.width - width - 10
                                anchors.verticalCenter: parent.verticalCenter
                                width: 20
                                height: 20
                                Image {
                                    id: arrowIcon
                                    source: "file:assets/icons/chevron-down.svg"
                                    visible: false
                                }
                                MultiEffect {
                                    source: arrowIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.buttonTextColor
                                }
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
                                rightPadding: control.indicator.width + control.spacing + 10
                                topPadding: 10
                                bottomPadding: 10
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
                        text: "Gallery"
                        color: theme.textColor
                        font.pixelSize: 20
                    }
                    
                    Label {
                        text: "Add or remove directories Photobase should scan"
                        color: theme.textColor
                        font.pixelSize: 14
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
                                IconButton {
                                    width: 20
                                    height: 20
                                    Layout.alignment: Qt.AlignBottom
                                    source: "file:assets/icons/plus.svg"
                                    color: theme.buttonTextColor
                                    onClicked: settingsController.addPath()
                                }

                                // Remove button
                                IconButton {
                                    width: 20
                                    height: 20
                                    Layout.alignment: Qt.AlignBottom
                                    source: "file:assets/icons/minus.svg"
                                    color: theme.buttonTextColor
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
                                Button {
                                    text: "Apply Changes"
                                    onClicked: settingsController.applyChanges()
                                    implicitHeight: 20
                                }
                            }
                        }
                    }
                }

                // About Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Label {
                        text: "About"
                        color: theme.textColor
                        font.pixelSize: 20
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
                                font.pixelSize: 14
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