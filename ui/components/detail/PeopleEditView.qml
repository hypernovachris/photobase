import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import ".." // For IconButton
import "../.." // For galleryModel if needed, but passing data is better

Item {
    id: peopleView
    
    property string currentImagePath: ""
    property var peopleList: []
    property int editingFaceId: -1
    
    signal backRequested()
    signal addPersonRequested()
    signal editPersonRequested(int faceId)
    signal removeFaceRequested(int faceId)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15
        
        // Header
        RowLayout {
            Layout.fillWidth: true
            
            ColumnLayout {
                spacing: 0
                Text {
                    text: currentImagePath ? (currentImagePath.split('\\').pop().split('/').pop()).toUpperCase() + "/" : ""
                    font.pixelSize: 14 // Smaller font
                    font.capitalization: Font.AllUppercase
                    color: theme.textColor
                    opacity: 0.7
                    Layout.fillWidth: true
                }

                Text {
                    text: "People"
                    font.pixelSize: 24
                    font.bold: true
                    color: theme.textColor
                }   
            }
            
            IconButton {
                width: 30
                height: 30
                iconSize: 30
                Layout.alignment: Qt.AlignTop | Qt.AlignRight
                source: "file:assets/icons/arrow-left.svg"
                onClicked: backRequested()
            }
        }
        
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: peopleList
            clip: true
            spacing: 10
            
            delegate: RowLayout {
                width: ListView.view.width
                spacing: 10
                
                // Face Crop
                Item {
                    id: faceWrapper
                    width: 60
                    height: 60
                    clip: true
                    
                    // Logic: If we have valid coordinates (w > 0), use crop. 
                    // If w=0 (manual add), use face_thumbnail_url.
                    
                    property bool isManual: (modelData.w === 0 && modelData.h === 0)
                    
                    // Case 1: Manual Thumbnail
                    Image {
                        source: faceWrapper.isManual ? (modelData.face_thumbnail_url || "") : ""
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectCrop
                        visible: faceWrapper.isManual && status === Image.Ready
                    }
                    
                    // Case 2: Crop from Main Image
                    Image {
                        id: cropImg
                        source: (!faceWrapper.isManual && currentImagePath) ? galleryModel.get_image_url(currentImagePath) : ""
                        autoTransform: true
                        asynchronous: true
                        fillMode: Image.Stretch 
                        visible: !faceWrapper.isManual
                        
                        property real faceW: modelData.w || 1
                        property real faceH: modelData.h || 1
                        property real faceX: modelData.x || 0
                        property real faceY: modelData.y || 0
                        
                        property real scaleFactor: 60 / Math.max(faceW, faceH)
                        
                        width: (sourceSize.width || 100) * scaleFactor
                        height: (sourceSize.height || 100) * scaleFactor
                        
                        x: -faceX * scaleFactor + (60 - faceW * scaleFactor) / 2
                        y: -faceY * scaleFactor + (60 - faceH * scaleFactor) / 2
                    }

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: theme.textColor
                        border.width: 1
                        visible: !cropImg.visible && !faceWrapper.isManual // Show placeholder/border if nothing else
                    }
                }
                
                // Name (Read Only)
                Text {
                    text: modelData.name || "Unnamed"
                    color: theme.textColor
                    font.pixelSize: 16
                    Layout.fillWidth: true
                }
                
                IconButton {
                    width: 20
                    height: 20
                    source: "file:assets/icons/pencil.svg"
                    onClicked: editPersonRequested(modelData.face_id)
                }

                IconButton {
                    width: 20
                    height: 20
                    source: "file:assets/icons/x.svg"
                    onClicked: removeFaceRequested(modelData.face_id)
                }
            }
            
            // Footer: Add Person Button
            footer: Item {
                width: ListView.view.width
                height: 50 // Enough space
                
                RowLayout {
                    anchors.fill: parent
                    anchors.topMargin: 10
                    spacing: 10
                    
                    // Plus Icon
                    Item {
                        width: 20
                        height: 20
                        
                        Image {
                            id: plusIcon
                            source: "file:assets/icons/plus.svg"
                            sourceSize.width: 20
                            sourceSize.height: 20
                            visible: false
                        }
                        
                        MultiEffect {
                            source: plusIcon
                            anchors.fill: parent
                            colorization: 1.0
                            colorizationColor: theme.textColor
                        }
                    }

                    Text {
                        text: "Add person..."
                        color: theme.textColor
                        font.pixelSize: 16
                    }
                    
                    Item { Layout.fillWidth: true }
                }
                
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: addPersonRequested()
                }
            }
        }
    }
}
