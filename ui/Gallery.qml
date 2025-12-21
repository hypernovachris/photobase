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
        
        // Scroll State Tracking
        property bool isScrolling: false
        signal checkVisibility()
        
        onContentYChanged: {
            isScrolling = true
            scrollStopTimer.restart()
        }
        
        property var selectedPaths: []
        
        Timer {
            id: scrollStopTimer
            interval: 150
            repeat: false
            onTriggered: {
                listView.isScrolling = false
                listView.checkVisibility()
            }
        }
        
        // Initial Setup and Dynamic Sizing
        function updateQueueLimit() {
            // Calculate how many 128x128 images fit on screen
            // Flow logic: (Available Width / (Item + Spacing))
            var availableWidth = listView.width - 20 // Padding
            var colCount = Math.floor((availableWidth + 10) / (128 + 10))
            if (colCount < 1) colCount = 1
            
            // Rows logic: Height / (Item + Spacing)
            var rowCount = Math.ceil(listView.height / (128 + 10))
            if (rowCount < 1) rowCount = 1
            
            // Total visible + buffer (one row extra)
            var visibleItems = colCount * (rowCount + 1)
            
            // console.log("Updating queue limit to: " + visibleItems)
            thumbnailGenerator.setMaxQueueSize(visibleItems)
        }
        
        Component.onCompleted: updateQueueLimit()
        onWidthChanged: updateQueueLimit()
        onHeightChanged: updateQueueLimit()
        
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
                        delegate: Item {
                            id: imageContainer
                            width: 128
                            height: 128
                            
                            property bool isVisible: false
                            
                            function calculateVisibility() {
                                if (listView.isScrolling) return
                                
                                var pos = mapToItem(listView, 0, 0)
                                if (pos.y < listView.height && pos.y + height > 0) {
                                    isVisible = true
                                } else {
                                    isVisible = false
                                }
                            }
                            
                            Connections {
                                target: listView
                                function onCheckVisibility() { calculateVisibility() }
                            }
                            
                            Component.onCompleted: calculateVisibility()
                            
                            Rectangle {
                                anchors.fill: parent
                                color: "#eeeeee"
                            }
                            
                            Image {
                                id: img
                                anchors.fill: parent
                                source: imageContainer.isVisible ? modelData.thumbnail : ""
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                
                                onStatusChanged: {
                                    if (status === Image.Error || status === Image.Null) {
                                        // Only request if we tried to load a real source and failed
                                        // Checking source != "" avoids infinite loop when we force-reload by setting source=""
                                        if (img.source != "" && imageContainer.isVisible && modelData && modelData.path) {
                                            thumbnailGenerator.request_thumbnail(modelData.path)
                                        }
                                    }
                                }
                                
                                Connections {
                                    target: thumbnailGenerator
                                    function onThumbnailReady(filePath, thumbPath) {
                                        if (modelData && filePath === modelData.path) {
                                            // Force reload and restore binding
                                            img.source = ""
                                            img.source = Qt.binding(function() { return imageContainer.isVisible ? modelData.thumbnail : "" })
                                        }
                                    }
                                }
                                
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            hoverEnabled: true
                            
                            onClicked: (mouse) => {
                                if (mouse.button === Qt.LeftButton) {
                                    if (mouse.modifiers & Qt.ControlModifier) {
                                        galleryModel.handle_selection(modelData.path, Qt.ControlModifier)
                                    } else if (mouse.modifiers & Qt.ShiftModifier) {
                                        galleryModel.handle_selection(modelData.path, Qt.ShiftModifier)
                                    } else {
                                        galleryModel.handle_selection(modelData.path, Qt.NoModifier)
                                    }
                                } else if (mouse.button === Qt.RightButton) {
                                    // If right-clicking something not selected, select it exclusively
                                    if (listView.selectedPaths.indexOf(modelData.path) === -1) {
                                        galleryModel.handle_selection(modelData.path, Qt.NoModifier)
                                    }
                                    contextMenu.popup()
                                }
                            }
                            
                            onDoubleClicked: (mouse) => {
                                if (mouse.button === Qt.LeftButton) {
                                    galleryModel.open_file(modelData.path)
                                }
                            }
                        }
                        
                        // Selection Overlay
                        Rectangle {
                            anchors.fill: parent
                            color: "transparent"
                            border.color: "#0078d4" // Windows Blue
                            border.width: 4
                            visible: listView.selectedPaths.indexOf(modelData.path) !== -1
                        }
                    }
                }
            }
        }
    }
    
    }
    }
    
    // Connections to Model
    Connections {
        target: galleryModel
        function onSelectionChanged(paths) {
            listView.selectedPaths = paths
        }
    }
    
    // Context Menu
    Menu {
        id: contextMenu
        MenuItem {
            text: "Open"
            onTriggered: {
                var paths = galleryModel.get_selected_paths()
                // Open all selected? Usually just the one focused or primary. 
                // Requirement says "Double clicking a thumbnail opens it". 
                // "Right clicking a thumbnail opens a context menu... Open..."
                // If multiple selected, "Open" usually opens all of them or just the one clicked?
                // Standard explorer opens all selected.
                // I will modify open_file to assume single path or handle list in backend?
                // The backend open_file takes one path.
                // Iterate client side or server side? 
                // Let's iterate here for now.
                 for (var i = 0; i < paths.length; i++) {
                     galleryModel.open_file(paths[i])
                 }
            }
        }
        MenuItem {
            text: "Reveal in File Explorer"
            onTriggered: {
                var paths = galleryModel.get_selected_paths()
                // Usually revealing multiple windows is annoying. Just reveal the last one or all?
                // Let's reveal all.
                 for (var i = 0; i < paths.length; i++) {
                     galleryModel.reveal_file(paths[i])
                 }
            }
        }
        MenuItem {
            text: "Edit Tags"
            enabled: false
        }
    }
}
