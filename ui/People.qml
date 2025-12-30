import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    
    Connections {
        target: galleryModel
        function onPeopleChanged() {
            refreshPeople()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        // anchors.margins: 20
        // spacing: 20

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Column {
                x: 20
                y: 20
                width: scrollView.availableWidth - 40
                spacing: 20

                Label {
                    text: "People"
                    color: theme.textColor
                    font.bold: true
                    font.pixelSize: 32
                }

                Flow {
                    width: parent.width
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
                                        source: person.faceThumbnail
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