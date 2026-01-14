import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import "components"

Rectangle {
    id: root
    anchors.fill: parent
    color: "#cc000000" // Semi-transparent black background
    visible: false
    focus: true // Enable keyboard focus
    
    // Auto-hide controls
    property bool controlsVisible: true
    Timer {
        id: hideControlsTimer
        interval: 1000
        repeat: false
        onTriggered: root.controlsVisible = false
    }
    
    function resetControlsTimer() {
        root.controlsVisible = true
        hideControlsTimer.restart()
    }
    
    // Navigation Functions
    function nextImage() {
        var path = galleryModel.get_next_image_path(root.currentImagePath)
        if (path) root.open(path)
    }
    
    function prevImage() {
        var path = galleryModel.get_previous_image_path(root.currentImagePath)
        if (path) root.open(path)
    }
    
    Keys.onRightPressed: nextImage()
    Keys.onLeftPressed: prevImage()
    Keys.onEscapePressed: {
        if (rightStack.currentIndex === 1) {
            rightStack.currentIndex = 0
        } else {
            root.close()
        }
    }
    
    // Trap mouse events & Track Activity
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
        onWheel: (wheel) => wheel.accepted = true
        onClicked: (mouse) => {
            root.resetControlsTimer()
            mouse.accepted = true
        }
        onPositionChanged: root.resetControlsTimer()
    }
    
    property string currentImagePath: ""
    
    signal closed()
    
    function open(path) {
        currentImagePath = path
        // Reset to info view
        if (detailPanel) detailPanel.resetToDetails()
        root.visible = true
        root.forceActiveFocus() // Ensure focus for keyboard
        root.resetControlsTimer()
        // Reset zoom
        if (zoomableImage) zoomableImage.resetZoom()
    }
    
    function close() {
        root.visible = false
        closed()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        
        // Left column: Image
        ZoomableImage {
            id: zoomableImage
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentImagePath: root.currentImagePath
            controlsVisible: root.controlsVisible
            onRequestNextImage: root.nextImage()
            onRequestPrevImage: root.prevImage()
            onInteractionOccurred: root.resetControlsTimer()
        }
        

        // Right column: info
        ImageDetailPanel {
            id: detailPanel
            Layout.fillHeight: true
            Layout.preferredWidth: 350
            Layout.maximumWidth: 400
            currentImagePath: root.currentImagePath
            onCloseRequested: root.close()
        }
    }
}