import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import QtQuick.Window

// Left Column: Image
Item {
    id: zoomableImageRoot

    property string currentImagePath: ""
    property bool controlsVisible: true
    
    signal requestNextImage()
    signal requestPrevImage()
    signal interactionOccurred()

    property real fitScale: (mainImage.sourceSize.width > 0 && mainImage.sourceSize.height > 0) ? 
                              Math.min(imageContainer.width / mainImage.sourceSize.width, imageContainer.height / mainImage.sourceSize.height) : 1.0
    property real minLocalScale: Math.min(1.0 / Screen.devicePixelRatio, fitScale)
    property real maxLocalScale: 4.0

    property bool scaleToFit: true

    onMinLocalScaleChanged: {
        if (mainImage.scale < minLocalScale) {
            mainImage.scale = minLocalScale
        }
        fixBounds()
    }

    onFitScaleChanged: {
        if (scaleToFit) {
            mainImage.scale = fitScale
            fixBounds()
        }
    }

    function fixBounds() {
        var scaledWidth = mainImage.width * mainImage.scale
        var scaledHeight = mainImage.height * mainImage.scale

        // X Axis
        if (scaledWidth < imageContainer.width) {
            mainImage.x = (imageContainer.width - scaledWidth) / 2
        } else {
            if (mainImage.x > 0) mainImage.x = 0
            if (mainImage.x < imageContainer.width - scaledWidth) mainImage.x = imageContainer.width - scaledWidth
        }

        // Y Axis
        if (scaledHeight < imageContainer.height) {
            mainImage.y = (imageContainer.height - scaledHeight) / 2
        } else {
            if (mainImage.y > 0) mainImage.y = 0
            if (mainImage.y < imageContainer.height - scaledHeight) mainImage.y = imageContainer.height - scaledHeight
        }
    }

    function resetZoom() {
        if (mainImage) {
            zoomableImageRoot.scaleToFit = true
            mainImage.scale = fitScale
            fixBounds()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "black"
        
        Item {
            id: imageContainer
            anchors.fill: parent
            clip: true
            
            onWidthChanged: zoomableImageRoot.fixBounds()
            onHeightChanged: zoomableImageRoot.fixBounds()

            Image {
                id: mainImage
                width: sourceSize.width
                height: sourceSize.height
                onWidthChanged: zoomableImageRoot.fixBounds()
                onHeightChanged: zoomableImageRoot.fixBounds()
                // source set via binding
                source: zoomableImageRoot.currentImagePath ? galleryModel.get_image_url(zoomableImageRoot.currentImagePath) : ""
                // fillMode removed to use intrinsic size
                asynchronous: true
                autoTransform: true 
                mipmap: true 
                transformOrigin: Item.TopLeft
                
                onStatusChanged: {
                    if (status === Image.Ready) {
                        zoomableImageRoot.resetZoom()
                    } else if (status === Image.Error) {
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
                    zoomableImageRoot.scaleToFit = false
                    var zoomFactor = 1.1
                    var oldScale = mainImage.scale
                    var newScale = oldScale
                    
                    if (wheel.angleDelta.y > 0) {
                        newScale *= zoomFactor
                    } else {
                        newScale /= zoomFactor
                    }
                    
                    // Limit minimum scale
                    if (newScale < zoomableImageRoot.minLocalScale) newScale = zoomableImageRoot.minLocalScale

                    // Limit maximum scale
                    if (newScale > zoomableImageRoot.maxLocalScale) newScale = zoomableImageRoot.maxLocalScale
                    
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
                    
                    // Re-clamp if we hit minLocalScale to re-center
                    if (mainImage.scale <= zoomableImageRoot.minLocalScale + 0.001) {
                        mainImage.scale = zoomableImageRoot.minLocalScale
                    }

                    fixBounds()

                    // Prevent default scrolling
                    wheel.accepted = true
                }
                
                onPressed: (mouse) => {
                    if (mainImage.scale > zoomableImageRoot.minLocalScale && mouse.button === Qt.LeftButton) {
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
                    if (isDragging && mainImage.scale >= zoomableImageRoot.minLocalScale) {
                        var dx = mouse.x - lastMousePos.x
                        var dy = mouse.y - lastMousePos.y
                        
                        mainImage.x += dx
                        mainImage.y += dy
                        
                        fixBounds()
                        
                        lastMousePos = Qt.point(mouse.x, mouse.y)
                    }
                }
            }
        }

        // Bar of buttons at the top
        // Bar of buttons at the top
        Rectangle {
            height: 32
            width: buttonRow.implicitWidth + 20
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 20
            visible: zoomableImageRoot.controlsVisible
            radius: 10
            color: "#80000000"
            
            RowLayout {
                id: buttonRow
                anchors.centerIn: parent
                spacing: 5
                // Reset Zoom (zoom to fit) Button
                IconButton {
                    Layout.alignment: Qt.AlignVCenter
                    source: "file:assets/icons/zoom_fit.svg"
                    color: "white"
                    onClicked: {
                        zoomableImageRoot.scaleToFit = true
                        // "Fit" behavior: Zoom to fit the screen, but clamp to max zoom limit.
                        // If fitScale > maxLocalScale, we cap at maxLocalScale.
                        mainImage.scale = Math.min(zoomableImageRoot.fitScale, zoomableImageRoot.maxLocalScale)
                        // If fitScale < minLocalScale (e.g. giant image), minLocalScale handles it? 
                        // Actually minLocalScale = min(1.0, fitScale). So if fitScale is small, it matches.
                        // We just want ensure we don't go below minLocalScale either?
                        if (mainImage.scale < zoomableImageRoot.minLocalScale) mainImage.scale = zoomableImageRoot.minLocalScale
                        
                        fixBounds()
                    }
                }
                // 1:1 zoom button
                IconButton {
                    Layout.alignment: Qt.AlignVCenter
                    source: "file:assets/icons/zoom_1to1.svg"
                    color: "white"
                    onClicked: {
                        zoomableImageRoot.scaleToFit = false
                        mainImage.scale = 1.0 / Screen.devicePixelRatio
                        fixBounds()
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