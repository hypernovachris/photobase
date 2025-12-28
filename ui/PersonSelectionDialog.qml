import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

Dialog {
    id: personDialog
    title: "Select Person"
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    
    property var peopleList: []
    property int selectedPersonId: -1
    
    signal personSelected(int personId)

    onOpened: {
        peopleList = galleryModel.get_people_model()
        personModel.model = peopleList
        selectedPersonId = -1 // Reset
    }

    onAccepted: {
        if (selectedPersonId !== -1) {
            personSelected(selectedPersonId)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Label {
            text: "Select a person:"
            font.bold: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            height: 300
            width: 300
            clip: true

            ListView {
                id: personModel
                model: peopleList
                delegate: ItemDelegate { // clickable row
                    width: ListView.view.width
                    highlighted: personDialog.selectedPersonId === modelData.id
                    
                    contentItem: RowLayout {
                        spacing: 10
                        
                        // Face Thumbnail
                        Image {
                            source: modelData.faceThumbnail
                            sourceSize.width: 40
                            sourceSize.height: 40
                            width: 40
                            height: 40
                            fillMode: Image.PreserveAspectCrop
                            
                            layer.enabled: true
                            layer.effect: MultiEffect {
                                maskEnabled: true
                                maskThresholdMin: 0.5
                                maskSpreadAtMin: 1.0
                                maskSource: ShaderEffectSource {
                                    sourceItem: Rectangle {
                                        width: 40; height: 40; radius: 20; color: "white"
                                    }
                                }
                            }
                            
                            // Placeholder if no thumbnail
                            Rectangle {
                                anchors.fill: parent
                                color: "grey"
                                visible: parent.status !== Image.Ready
                                radius: 20
                            }
                        }

                        Text {
                            text: modelData.name || "Unknown"
                            Layout.fillWidth: true
                        }
                    }
                    
                    onClicked: {
                        personDialog.selectedPersonId = modelData.id
                    }
                }
            }
        }
    }
}
