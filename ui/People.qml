import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    
    // Scan Progress State
    property int scanProcessed: 0
    property int scanTotal: 0
    property bool isScanning: false

    Connections {
        target: galleryModel
        function onScanProgress(processed, total) {
            isScanning = true
            scanProcessed = processed
            scanTotal = total
        }
        function onScanFinished() {
            isScanning = false
            scanProcessed = 0
            scanTotal = 0
            refreshPeople()
        }
        function onPeopleChanged() {
            refreshPeople()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            spacing: 20

            Label {
                text: "People"
                color: theme.textColor
                font.bold: true
                font.pixelSize: 32
            }
            
            Item { Layout.fillWidth: true }
            
            Button {
                text: root.isScanning ? "Scanning..." : "Scan Faces"
                enabled: !root.isScanning
                onClicked: galleryModel.start_face_scan()
            }
        }
        
        // Progress Bar
        ColumnLayout {
            visible: root.isScanning
            Layout.fillWidth: true
            spacing: 5
            
            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: root.scanTotal > 0 ? root.scanTotal : 1
                value: root.scanProcessed
            }
            Label {
                text: "Scanning " + root.scanProcessed + " / " + root.scanTotal
                color: theme.secondaryTextColor
            }
        }

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Flow {
                width: scrollView.availableWidth
                spacing: 20
                padding: 10
                
                Repeater {
                    model: peopleModel
                    
                    delegate: Item {
                        width: 160
                        height: 240 // Taller for inputs
                        
                        property var person: modelData
                        
                        Column {
                            anchors.centerIn: parent
                            spacing: 8
                            
                            // Face Card
                            Rectangle {
                                width: 140
                                height: 140
                                color: theme.buttonColor
                                border.color: hoverArea.containsMouse ? theme.highlightColor : theme.borderColor
                                border.width: hoverArea.containsMouse ? 2 : 1
                                
                                Image {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    source: person.imagePath
                                    
                                    // Face Crop
                                    sourceClipRect: Qt.rect(person.faceRect.x, person.faceRect.y, person.faceRect.w, person.faceRect.h)
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                }
                                
                                MouseArea {
                                    id: hoverArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        galleryModel.set_person_filter(person.id)
                                    }
                                }
                            }
                            
                            // Name Input
                            TextField {
                                width: 140
                                text: person.name
                                placeholderText: "Name this person..."
                                color: theme.textColor
                                background: Rectangle { color: "transparent" }
                                horizontalAlignment: TextInput.AlignHCenter
                                font.bold: true
                                font.pixelSize: 14
                                
                                onEditingFinished: {
                                    if (text !== person.name) {
                                        galleryModel.rename_person(person.id, text)
                                    }
                                    focus = false
                                }
                            }
                            
                            Text {
                                text: person.count + " Photos"
                                font.pixelSize: 12
                                color: theme.secondaryTextColor
                                width: parent.width
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }
            }
        }
    }
    
    property var peopleModel: []
    
    function refreshPeople() {
        peopleModel = galleryModel.get_people_model()
    }
    
    onVisibleChanged: {
        if (visible) refreshPeople()
    }
    
    Component.onCompleted: refreshPeople()
}
