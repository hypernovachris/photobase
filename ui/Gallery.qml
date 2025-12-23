import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    property string activeFilter: ""
    Connections {
        target: galleryModel
        function onFilterChanged(tagName) {
            activeFilter = tagName
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Filter Banner
        Rectangle {
            Layout.fillWidth: true
            height: 50
            color: theme.isDark ? "#1e3a5f" : "#e3f2fd"
            visible: activeFilter !== ""
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 10
                
                Label {
                    text: "Filtered by tag: <b>" + activeFilter + "</b>"
                    color: theme.textColor
                    font.pixelSize: 16
                    Layout.fillWidth: true
                }
                
                Button {
                    text: "Clear Filter"
                    onClicked: galleryModel.clear_tag_filter()
                }
            }
        }

        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20
            clip: true
            interactive: false
            cacheBuffer: 1000
            reuseItems: true
            flickDeceleration: 10000
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            footer: Item {
                height: 50
            }
            model: galleryModel
        
            // Scroll State Tracking
            property bool isScrolling: false
            signal checkVisibility()
            
            onContentYChanged: {
                isScrolling = true
                if (!scrollCheckTimer.running) {
                    scrollCheckTimer.start()
                }
                scrollStopTimer.restart()
            }
            
            property var selectedPaths: []
            
            // Periodically check visibility while scrolling
            Timer {
                id: scrollCheckTimer
                interval: 50
                repeat: true
                onTriggered: listView.checkVisibility()
            }
            
            // Detect when scrolling stops
            Timer {
                id: scrollStopTimer
                interval: 150
                repeat: false
                onTriggered: {
                    listView.isScrolling = false
                    scrollCheckTimer.stop()
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
                        color: theme.textColor
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
                                    // if (listView.isScrolling) return // Removed to allow updates during scroll
                                    
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
                                    color: theme.buttonColor
                                }
                                
                                Image {
                                    id: img
                                    anchors.fill: parent
                                    source: imageContainer.isVisible ? modelData.thumbnail : ""
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    
                                    onStatusChanged: {
                                        if (status === Image.Error || status === Image.Null) {
                                            if (img.source != "" && imageContainer.isVisible && modelData && modelData.path) {
                                                thumbnailGenerator.request_thumbnail(modelData.path)
                                            }
                                        }
                                    }
                                    
                                    Connections {
                                        target: thumbnailGenerator
                                        function onThumbnailReady(filePath, thumbPath) {
                                            if (modelData && filePath === modelData.path) {
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
                                        border.color: theme.highlightColor
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
                 for (var i = 0; i < paths.length; i++) {
                     galleryModel.open_file(paths[i])
                 }
            }
        }
        MenuItem {
            text: "Reveal in File Explorer"
            onTriggered: {
                var paths = galleryModel.get_selected_paths()
                 for (var i = 0; i < paths.length; i++) {
                     galleryModel.reveal_file(paths[i])
                 }
            }
        }
        MenuItem {
            text: "Edit Tags"
            enabled: listView.selectedPaths.length > 0
            onTriggered: {
                tagDialog.open()
            }
        }
    }

    TagEditDialog {
        id: tagDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 300
        height: 400
    }
}