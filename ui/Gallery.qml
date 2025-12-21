import QtQuick
import QtQuick.Controls

Item {
    ListView {
        id: listView
        anchors.fill: parent
        spacing: 20
        clip: true
        interactive: false
        cacheBuffer: 1000
        reuseItems: true
        flickDeceleration: 10000
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        model: galleryModel
        
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: (wheel) => {
                listView.flick(0, wheel.angleDelta.y * 500)
                wheel.accepted = true
            }
        }
        
        delegate: Item {
            width: ListView.view.width
            // Deterministic height calculation
            property int flowPadding: 20
            property int imageSize: 128
            property int flowSpacing: 10
            property int headerHeight: 40
            
            // Calculate available width for images
            property int availableWidth: width - flowPadding
            // Calculate items per row (columns)
            property int columns: Math.floor((availableWidth + flowSpacing) / (imageSize + flowSpacing))
            // Calculate total rows needed
            property int rows: Math.ceil(images.length / Math.max(1, columns))
            
            // Explicit height: Header + (Rows * ImageHeight) + ((Rows-1) * Spacing)
            height: headerHeight + (rows * imageSize) + (rows > 0 ? (rows - 1) * flowSpacing : 0)

            Column {
                anchors.fill: parent
                spacing: 10
                
                Label {
                    height: 30 // Part of header height
                    text: monthText
                    font.bold: true
                    font.pixelSize: 20
                    leftPadding: 10
                    verticalAlignment: Text.AlignVCenter
                }
                
                Flow {
                    width: parent.width - 20 // Padding
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10
                    
                    Repeater {
                        model: images
                        delegate: Image {
                            source: modelData.thumbnail
                            width: 128
                            height: 128
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            
                            onStatusChanged: {
                                if (status === Image.Error || status === Image.Null) {
                                    if (modelData && modelData.path) {
                                        thumbnailGenerator.request_thumbnail(modelData.path)
                                    }
                                }
                            }
                            
                            Connections {
                                target: thumbnailGenerator
                                function onThumbnailReady(filePath, thumbPath) {
                                    if (modelData && filePath === modelData.path) {
                                        // Force reload
                                        var oldSource = source
                                        source = ""
                                        source = oldSource
                                    }
                                }
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    console.log("Clicked image: " + modelData.path)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
