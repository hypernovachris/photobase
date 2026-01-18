import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import "components"

Item {
    onVisibleChanged: {
        if (visible) {
            delayedVisibilityCheckTimer.restart()
        }
    }
    property string activeFilter: ""
    Connections {
        target: galleryModel
        function onFilterChanged(tagName) {
            activeFilter = tagName
            listView.checkVisibility()
            imageViewer.close()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: listView
                anchors.fill: parent
                spacing: 20
                clip: true
                interactive: true 
                cacheBuffer: 1000
                reuseItems: true
                flickDeceleration: 10000
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: null
                
                header: Column {
                    width: listView.width
                    spacing: 20
                    padding: 20

                    RowLayout {
                        spacing: 10

                        // Back Button
                        IconButton {
                            width: 30
                            height: 30
                            iconSize: 30
                            visible: activeFilter !== ""
                            source: "file:assets/icons/arrow-left.svg"
                            onClicked: galleryModel.clear_tag_filter()
                        }

                        Label {
                            text: activeFilter !== "" ? activeFilter : "Gallery"
                            color: theme.textColor
                            font.bold: true
                            font.pixelSize: 32
                        }
                    }
                }
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
                    interval: 200
                    repeat: true
                    onTriggered: listView.checkVisibility()
                }
                
                
                Timer {
                    id: delayedVisibilityCheckTimer
                    interval: 100
                    repeat: false
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
                        delayedVisibilityCheckTimer.restart()
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

                function getMonthHeight(monthIndex) {
                    var imgCount = galleryModel.getImageCountForMonth(monthIndex);
                    if (imgCount === 0) return 0;

                    var flowPadding = 20;
                    var imageSize = 128;
                    var flowSpacing = 10;
                    var headerHeight = 40;

                    var availableWidth = listView.width - flowPadding;
                    var colCount = Math.floor((availableWidth + flowSpacing) / (imageSize + flowSpacing));
                    if (colCount < 1) colCount = 1;

                    var rowCount = Math.ceil(imgCount / colCount);
                    var totalHeight = headerHeight + (rowCount * imageSize) + (rowCount > 0 ? (rowCount - 1) * flowSpacing : 0);

                    return totalHeight;
                }

                Connections {
                    target: galleryModel
                    // When images are added/removed, we must recalculate the total height
                    function onCountChanged() {
                        listView.recalculateGeometry()
                    }
                    // If your model resets completely
                    function onModelReset() {
                        listView.recalculateGeometry()
                    }
                }

                property real cachedTotalHeight: 0

                function recalculateGeometry() {
                    cachedTotalHeight = calculateTotalHeight();
                }

                function calculateTotalHeight() {
                    var totalHeight = 0;
                    for (var i = 0; i < galleryModel.count; i++) {
                        totalHeight += getMonthHeight(i);
                    }
                    return totalHeight;
                }

                function calculateRealContentY() {
                    // 1. Robust Index Lookup: Check a few points to avoid missing items due to spacing/padding
                    var topIndex = -1
                    // Scan down 50 pixels in 10px steps to find the first actual item
                    for (var offset = 0; offset <= 50; offset += 10) {
                        topIndex = listView.indexAt(10, listView.contentY + offset)
                        if (topIndex !== -1) break
                    }
                    
                    // If we still can't find an item (e.g. empty list or overscroll), return 0 to be safe
                    if (topIndex === -1) return 0 
                    
                    var heightBefore = 0
                    for (var i = 0; i < topIndex; i++) {
                        heightBefore += getMonthHeight(i)
                    }
                    
                    var currentItem = listView.itemAt(10, listView.contentY + offset) // Use the same offset that found the index
                    if (currentItem) {
                        // Map the item's position to finding how much is scrolled off
                        var itemOffset = listView.contentY - currentItem.y
                        heightBefore += Math.max(0, itemOffset)
                    }
                    
                    return heightBefore
                }
                
                Component.onCompleted: {
                    updateQueueLimit()
                    listView.checkVisibility()
                    recalculateGeometry()
                }
                onWidthChanged: {
                    recalculateGeometry()
                    updateQueueLimit()
                    listView.isScrolling = true
                    if (!scrollCheckTimer.running) {
                        scrollCheckTimer.start()
                    }
                    scrollStopTimer.restart()
                }
                onHeightChanged: {
                    updateQueueLimit()
                    listView.isScrolling = true
                    if (!scrollCheckTimer.running) {
                        scrollCheckTimer.start()
                    }
                    scrollStopTimer.restart()
                }
                
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

                    // Calculate effective width of the grid content
                    property int gridWidth: (columns * imageSize) + (Math.max(0, columns - 1) * flowSpacing)

                    Column {
                        anchors.fill: parent
                        spacing: 10
                        
                        Label {
                            height: 30 // Part of header height
                            text: monthText
                            color: theme.textColor
                            font.bold: true
                            font.pixelSize: 20
                            anchors.left: parent.left
                            anchors.leftMargin: (parent.width - gridWidth) / 2
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        Flow {
                            width: gridWidth
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
                                        var pos = mapToItem(listView, 0, 0)
                                        if (pos.y < listView.height && pos.y + height > 0) {
                                            isVisible = true
                                        } else {
                                            isVisible = false
                                        }
                                    }
                                    
                                    Connections {
                                        target: listView
                                        function onCheckVisibility() { 
                                            calculateVisibility()
                                        }
                                    }
                                    
                                    Component.onCompleted: {
                                        calculateVisibility()
                                    }
                                    
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
                                                    imageViewer.open(modelData.path)
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

            ScrollBar {
                id: customScrollBar
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                policy: ScrollBar.AlwaysOn
                
                // Calculate Size
                // Use Math.max on the divisor to prevent division by zero or negative size
                size: listView.height / Math.max(listView.height, listView.cachedTotalHeight)
                
                // 1. BINDING FIX: Only bind 'position' when the user is NOT dragging.
                // This prevents the calculation from fighting the user's mouse movement.
                Binding {
                    target: customScrollBar
                    property: "position"
                    value: listView.calculateRealContentY() / Math.max(listView.height, listView.cachedTotalHeight)
                    when: !customScrollBar.pressed
                }
                
                // 2. DRAG LOGIC: Update the view when the user moves the handle
                onPositionChanged: {
                    if (pressed) {
                        var targetY = position * listView.cachedTotalHeight
                        
                        var currentSum = 0
                        for (var i = 0; i < galleryModel.count; i++) {
                            var h = listView.getMonthHeight(i)
                            if (currentSum + h > targetY) {
                                // Position the view at the start of the month
                                listView.positionViewAtIndex(i, ListView.Beginning)
                                // Fine-tune the offset (scroll into the month)
                                listView.contentY += (targetY - currentSum)
                                break
                            }
                            currentSum += h
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
                     // galleryModel.open_file(paths[i])
                     imageViewer.open(paths[i])
                     // Only open the first one for now in viewer to avoid spamming or logic complexity
                     break; 
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
            text: listView.selectedPaths.length > 1 ? "Add Tag" : "Edit Tags"
            enabled: listView.selectedPaths.length > 0
            onTriggered: {
                tagDialog.isAddMode = listView.selectedPaths.length > 1
                tagDialog.open()
            }
        }
        MenuItem {
            text: "Remove from '" + activeFilter + "'"
            visible: activeFilter !== "" && listView.selectedPaths.length > 0
            height: visible ? implicitHeight : 0
            onTriggered: {
                galleryModel.remove_selection_from_active_filter()
            }
        }
    }

    TagEditDialog {
        id: tagDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 300

        height: 400
        property bool isAddMode: false
    }

    ImageViewer {
        id: imageViewer
        z: 100 // Ensure it is on top
        onClosed: {
            listView.checkVisibility()
            // cleanup
        }
    }
}