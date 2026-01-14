import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

// Left Column: Image
Item {
    id: zoomableImageRoot

    property string currentImagePath: ""
    property bool controlsVisible: true
    
    signal requestNextImage()
    signal requestPrevImage()
    signal interactionOccurred()

    function resetZoom() {
        if (mainImage) {
            mainImage.scale = 1.0
            mainImage.x = 0
            mainImage.y = 0
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "black"
        
        Item {
            id: imageContainer
            anchors.fill: parent
            clip: true

            Image {
                id: mainImage
                width: parent.width
                height: parent.height
                source: zoomableImageRoot.currentImagePath ? galleryModel.get_image_url(zoomableImageRoot.currentImagePath) : ""
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                autoTransform: true 
                transformOrigin: Item.TopLeft
                
                onStatusChanged: {
                    if (status === Image.Error) {
                        console.error("ImageViewer: Failed to load image:", source)
                    }
                }
            }
            
            MouseArea {
                id: imageMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                
                property point lastMousePos
                property bool isDragging: false

                onWheel: (wheel) => {
                    var zoomFactor = 1.1
                    var oldScale = mainImage.scale
                    var newScale = oldScale
                    
                    if (wheel.angleDelta.y > 0) {
                        newScale *= zoomFactor
                    } else {
                        newScale /= zoomFactor
                    }
                    
                    // Limit minimum scale to 1.0
                    if (newScale < 1.0) newScale = 1.0

                    // Limit maximum scale to 100.0
                    if (newScale > 100.0) newScale = 100.0
                    
                    // Calculate new position to zoom towards mouse
                    var mouseX = wheel.x
                    var mouseY = wheel.y
                    
                    var xInImage = (mouseX - mainImage.x) / oldScale
                    var yInImage = (mouseY - mainImage.y) / oldScale
                    
                    var newX = mouseX - xInImage * newScale
                    var newY = mouseY - yInImage * newScale
                    
                    // Apply changes
                    mainImage.scale = newScale
                    mainImage.x = newX
                    mainImage.y = newY
                    
                    // Re-clamp if we hit 1.0 to re-center (optional logic, but keeps it clean)
                    if (mainImage.scale <= 1.001) {
                        mainImage.scale = 1.0
                        mainImage.x = 0
                        mainImage.y = 0
                    }

                    // Prevent default scrolling
                    wheel.accepted = true
                }
                
                onPressed: (mouse) => {
                    if (mainImage.scale > 1.0 && mouse.button === Qt.LeftButton) {
                        lastMousePos = Qt.point(mouse.x, mouse.y)
                        isDragging = true
                    }
                    zoomableImageRoot.interactionOccurred()
                }
                
                onReleased: {
                    isDragging = false
                }
                
                onPositionChanged: (mouse) => {
                    zoomableImageRoot.interactionOccurred()
                    if (isDragging && mainImage.scale > 1.0) {
                        var dx = mouse.x - lastMousePos.x
                        var dy = mouse.y - lastMousePos.y
                        
                        mainImage.x += dx
                        mainImage.y += dy
                        
                        lastMousePos = Qt.point(mouse.x, mouse.y)
                    }
                }
            }
        }

        // Reset Zoom Button
        Item {
            width: 32
            height: 32
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 20
            visible: mainImage.scale > 1.0
            
            Rectangle {
                anchors.fill: parent
                radius: 10
                color: "#80000000"
                
                IconButton {
                    anchors.fill: parent
                    source: "file:assets/icons/scan.svg"
                    color: "white"
                    hoverColor: "white" // Keep it simple or add hover effect if desired
                    onClicked: {
                        mainImage.scale = 1.0
                        mainImage.x = 0
                        mainImage.y = 0
                    }
                }
            }
        }
        
        // Left Arrow
        Item {
            width: 32
            height: 32
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 20
            visible: zoomableImageRoot.controlsVisible
            opacity: visible ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 200 } }
            
            Rectangle {
                anchors.fill: parent
                radius: 10
                color: "#80000000" // Semi-transparent black
                
                IconButton {
                    anchors.fill: parent
                    source: "file:assets/icons/arrow-left.svg"
                    color: "white" 
                    onClicked: zoomableImageRoot.requestPrevImage()
                    onEntered: zoomableImageRoot.interactionOccurred() // Keep the keep-alive logic
                }
            }
        }
        
        // Right Arrow
        Item {
            width: 32
            height: 32
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 20
            visible: zoomableImageRoot.controlsVisible
            opacity: visible ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 100 } }
            
            Rectangle {
                anchors.fill: parent
                radius: 10
                color: "#80000000"
                
                IconButton {
                    anchors.fill: parent
                    source: "file:assets/icons/arrow-right.svg"
                    color: "white"
                    onClicked: zoomableImageRoot.requestNextImage()
                    onEntered: zoomableImageRoot.interactionOccurred()
                }
            }
        }
    }
}