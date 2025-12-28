import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

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
    property var currentImageDetails: null
    property var peopleList: []
    
    signal closed()
    
    function open(path) {
        currentImagePath = path
        currentImageDetails = galleryModel.get_image_details(path)
        peopleList = galleryModel.get_people_in_image(path)
        // Reset to info view
        rightStack.currentIndex = 0
        root.visible = true
        root.forceActiveFocus() // Ensure focus for keyboard
        root.resetControlsTimer()
        // Reset zoom
        if (mainImage) {
            mainImage.scale = 1.0
            mainImage.x = 0
            mainImage.y = 0
        }
    }
    
    function close() {
        root.visible = false
        closed()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        
        // Left Column: Image
        Rectangle {
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "black"
            
            Item {
                id: imageContainer
                anchors.fill: parent
                clip: true

                Image {
                    id: mainImage
                    width: parent.width
                    height: parent.height
                    source: root.currentImagePath ? "file:///" + root.currentImagePath : ""
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    autoTransform: true 
                    transformOrigin: Item.TopLeft
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
                        root.resetControlsTimer()
                    }
                    
                    onReleased: {
                        isDragging = false
                    }
                    
                    onPositionChanged: (mouse) => {
                        root.resetControlsTimer()
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
                    
                    Image {
                        id: resetIcon
                        source: "file:assets/icons/scan.svg"
                        anchors.centerIn: parent
                        visible: false
                    }
                    
                    MultiEffect {
                        anchors.margins: 6
                        source: resetIcon
                        anchors.fill: parent
                        colorization: 1.0
                        colorizationColor: "white"
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        mainImage.scale = 1.0
                        mainImage.x = 0
                        mainImage.y = 0
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
                visible: root.controlsVisible
                opacity: visible ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 200 } }
                
                Rectangle {
                    anchors.fill: parent
                    radius: 10
                    color: "#80000000" // Semi-transparent black
                    
                    Image {
                        source: "file:assets/icons/arrow-left.svg"
                        anchors.centerIn: parent
                        visible: false
                    }
                    
                    MultiEffect {
                        source: parent.children[0]
                        anchors.fill: parent
                        colorization: 1.0
                        colorizationColor: "white"
                        anchors.margins: 6
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onEntered: root.resetControlsTimer()
                    onClicked: root.prevImage()
                }
            }
            
            // Right Arrow
            Item {
                width: 32
                height: 32
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 20
                visible: root.controlsVisible
                opacity: visible ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 100 } }
                
                Rectangle {
                    anchors.fill: parent
                    radius: 10
                    color: "#80000000"
                    
                    Image {
                        source: "file:assets/icons/arrow-right.svg"
                        anchors.centerIn: parent
                        visible: false
                    }
                    
                    MultiEffect {
                        source: parent.children[0]
                        anchors.fill: parent
                        colorization: 1.0
                        colorizationColor: "white"
                        anchors.margins: 6
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onEntered: root.resetControlsTimer()
                    onClicked: root.nextImage()
                }
            }

        }
        
        // Right Column: Info
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 350
            Layout.maximumWidth: 400
            color: theme.backgroundColor
            
            StackLayout {
                id: rightStack
                anchors.fill: parent
                currentIndex: 0
                
                // View 0: Image Detail
                Item {
                    id: detailView
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15
                        
                        // Header: Filename + Close
                        RowLayout {
                            Layout.fillWidth: true
                            
                            Text {
                                text: root.currentImagePath ? root.currentImagePath.split('\\').pop().split('/').pop() : ""
                                font.pixelSize: 24
                                font.bold: true
                                color: theme.textColor
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                                
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        galleryModel.open_file(root.currentImagePath)
                                    }
                                }
                            }

                            // Spacer
                            Item {
                                Layout.fillWidth: true
                            }
                            
                            Item {
                                width: 30
                                height: 30
                                Layout.alignment: Qt.AlignVCenter

                                Image {
                                    id: closeIcon
                                    source: "file:assets/icons/x.svg" 
                                    sourceSize.width: 30
                                    sourceSize.height: 30
                                    visible: false
                                }

                                MultiEffect {
                                    id: effect
                                    source: closeIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    // anchors.margins: -10 
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        root.close()
                                    }
                                }
                            }
                        }
                        
                        // Path
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignLeft
                            spacing: 10
                            
                            // Hard drive icon
                            Item {
                                width: 20
                                height: 20
                                Image {
                                    id: hardDriveIcon
                                    source: "file:assets/icons/hard-drive.svg" 
                                    sourceSize.width: 20
                                    sourceSize.height: 20
                                    visible: false  
                                }
                                MultiEffect {
                                    source: hardDriveIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }
                            }
                            
                            Text {
                                text: root.currentImagePath ? root.currentImagePath.substring(0, root.currentImagePath.lastIndexOf(root.currentImagePath.split('\\').pop().split('/').pop())).slice(0, -1) : ""
                                font.pixelSize: 14
                                color: theme.textColor
                                elide: Text.ElideMiddle
                                Layout.fillWidth: true
                                
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        galleryModel.reveal_file(root.currentImagePath)
                                    }
                                }
                            }
                        }
                        
                        // Date
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignLeft
                            spacing: 10
                            // Clock icon
                            Item {
                                width: 20
                                height: 20
                                Image {
                                    id: clockIcon
                                    source: "file:assets/icons/clock.svg" 
                                    sourceSize.width: 20
                                    sourceSize.height: 20
                                    visible: false  
                                }
                                MultiEffect {
                                    source: clockIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }
                            }
                            Text {
                                text: root.currentImageDetails ? root.currentImageDetails.date : ""
                                font.pixelSize: 14
                                color: theme.textColor
                            }
                        }

                        // EXIF Data
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignLeft
                            spacing: 10
                            // Aperture icon
                            Item {
                                width: 20
                                height: 20
                                Image {
                                    id: apertureIcon
                                    source: "file:assets/icons/aperture.svg" 
                                    sourceSize.width: 20
                                    sourceSize.height: 20
                                    visible: false  
                                }
                                MultiEffect {
                                    source: apertureIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }
                            }
                            Text {
                                text: root.currentImageDetails ? root.currentImageDetails.exifString : "Unavailable"
                                font.pixelSize: 14
                                color: theme.textColor
                            }
                        }
                        
                        // Tags
                        Flow {
                            Layout.fillWidth: true
                            spacing: 10
                            readonly property int rowHeight: 30

                            // Tags icon
                            Item {
                                height: parent.rowHeight
                                width: 20
                                Item {
                                    width: 20
                                    height: 20
                                    anchors.centerIn: parent
                                    Image {
                                        id: tagsIcon
                                        source: "file:assets/icons/tag.svg" 
                                        sourceSize.width: 20
                                        sourceSize.height: 20
                                        visible: false  
                                    }
                                    MultiEffect {
                                        source: tagsIcon
                                        anchors.fill: parent
                                        colorization: 1.0
                                        colorizationColor: theme.textColor
                                    }
                                }
                            }

                            // None Label
                            Text {
                                height: parent.rowHeight
                                text: "(None)"
                                font.pixelSize: 14
                                color: theme.textColor
                                visible: root.currentImageDetails ? root.currentImageDetails.tags.length === 0 : true
                                verticalAlignment: Text.AlignVCenter
                            }

                            // Tags
                            Repeater {
                                visible: root.currentImageDetails ? root.currentImageDetails.tags.length > 0 : false
                                model: root.currentImageDetails ? root.currentImageDetails.tags : []
                                delegate: Rectangle {
                                    height: 30
                                    width: tagRow.implicitWidth + 10
                                    radius: 15
                                    color: theme.buttonColor
                                    // border.color: theme.textColor
                                    // border.width: 1
                                    
                                    Row {
                                        id: tagRow
                                        anchors.centerIn: parent
                                        spacing: 5
                                        padding: 5
                                        
                                        Text {
                                            text: modelData
                                            color: theme.buttonTextColor
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        
                                        Item {
                                            width: 16
                                            height: 16
                                            anchors.verticalCenter: parent.verticalCenter

                                            Image {
                                                id: removeIcon
                                                source: "file:assets/icons/x.svg" 
                                                sourceSize.width: 16
                                                sourceSize.height: 16
                                                visible: false
                                            }

                                            MultiEffect {
                                                id: effect
                                                source: removeIcon
                                                anchors.fill: parent
                                                colorization: 1.0
                                                colorizationColor: theme.buttonTextColor
                                            }

                                            MouseArea {
                                                anchors.fill: parent
                                                // anchors.margins: -10 
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    galleryModel.remove_tag_from_image_path(root.currentImagePath, modelData)
                                                    root.currentImageDetails = galleryModel.get_image_details(root.currentImagePath)
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            // Add Tag Button
                            Item {
                                height: parent.rowHeight
                                width: 20
                                Item {
                                    width: 20
                                    height: 20
                                    visible: true
                                    anchors.verticalCenter: parent.verticalCenter
                                    Image {
                                        id: addIcon
                                        source: "file:assets/icons/plus.svg" 
                                        sourceSize.width: 20
                                        sourceSize.height: 20
                                        visible: false
                                    }

                                    MultiEffect {
                                        id: addEffect
                                        source: addIcon
                                        anchors.fill: parent
                                        colorization: 1.0
                                        colorizationColor: theme.textColor
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            tagDialog.targetPath = root.currentImagePath
                                            tagDialog.isAddMode = true
                                            tagDialog.open()
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Location (Placeholder)
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignLeft
                            spacing: 10
                            // Pin icon
                            Item {
                                height: 20
                                width: 20
                                Image {
                                    id: pinIcon
                                    source: "file:assets/icons/map-pin.svg"
                                    sourceSize.width: 20
                                    sourceSize.height: 20
                                    visible: false
                                }
                                MultiEffect {
                                    source: pinIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }
                            }
                            Text {
                                text: "No location data"
                                font.italic: true
                                color: theme.textColor
                                opacity: 0.7
                            }
                        }
                        
                        // People
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignLeft
                            spacing: 10

                            // People icon
                            Item {
                                height: 20
                                width: 20
                                Image {
                                    id: peopleIcon
                                    source: "file:assets/icons/scan-face.svg"
                                    sourceSize.width: 20
                                    sourceSize.height: 20
                                    visible: false
                                }
                                MultiEffect {
                                    source: peopleIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }
                            }

                            // Label
                            Item {
                                // 1. Give the container a size based on its content
                                implicitWidth: peopleRow.implicitWidth
                                implicitHeight: peopleRow.implicitHeight
                                
                                // Allow it to be positioned within your external Layout
                                Layout.fillWidth: false 

                                // 2. The Layout handles the horizontal positioning
                                RowLayout {
                                    id: peopleRow
                                    anchors.fill: parent
                                    spacing: 10
                                    
                                    Text {
                                        text: (root.peopleList ? root.peopleList.length : "None") + " detected"
                                        color: theme.textColor
                                        verticalAlignment: Text.AlignVCenter
                                    }

                                    // Link icon
                                    Item {
                                        width: 16
                                        height: 16
                                        Layout.alignment: Qt.AlignVCenter

                                        Image {
                                            id: linkIcon
                                            source: "file:assets/icons/external-link-3px.svg"
                                            sourceSize: Qt.size(16, 16)
                                            visible: false
                                        }

                                        MultiEffect {
                                            source: linkIcon
                                            anchors.fill: parent
                                            colorization: 1.0
                                            colorizationColor: theme.textColor
                                        }
                                    }
                                }

                                // 3. The MouseArea fills the entire Item (Text + Icon)
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        rightStack.currentIndex = 1
                                    }
                                }
                            }
                        }
                        Item { Layout.fillHeight: true }
                    }
                }
                
                // View 1: People Edit View
                Item {
                    id: peopleView
                    
                    property int editingFaceId: -1 // Track which face we are editing if any
                    
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
                                    // Filename in All Caps and Smaller Font + "/"
                                    text: root.currentImagePath ? (root.currentImagePath.split('\\').pop().split('/').pop()).toUpperCase() + "/" : ""
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
                            
                            // Back Button
                            Item {
                                width: 30
                                height: 30
                                Layout.alignment: Qt.AlignTop | Qt.AlignRight

                                Image {
                                    id: backIcon
                                    source: "file:assets/icons/arrow-left.svg" 
                                    sourceSize.width: 30
                                    sourceSize.height: 30
                                    visible: false
                                }

                                MultiEffect {
                                    id: backIconEffect
                                    source: backIcon
                                    anchors.fill: parent
                                    colorization: 1.0
                                    colorizationColor: theme.textColor
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        rightStack.currentIndex = 0
                                    }
                                }
                            }
                        }
                        
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: root.peopleList
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
                                        source: (!faceWrapper.isManual && root.currentImagePath) ? "file:///" + root.currentImagePath : ""
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
                                
                                // Edit Icon (Pencil)
                                Item {
                                    width: 20
                                    height: 20
                                    visible: true 
                                    
                                    Image {
                                        id: editIcon
                                        source: "file:assets/icons/pencil.svg"
                                        sourceSize.width: 20
                                        sourceSize.height: 20
                                        visible: false
                                    }
                                    
                                    MultiEffect {
                                        source: editIcon
                                        anchors.fill: parent
                                        colorization: 1.0
                                        colorizationColor: theme.textColor
                                    }
                                    
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            peopleView.editingFaceId = modelData.face_id
                                            personSelectionDialog.title = "Replace Person"
                                            personSelectionDialog.open()
                                        }
                                    }
                                }

                                // Delete Icon (X)
                                Item {
                                    width: 20
                                    height: 20
                                    
                                    Image {
                                        id: delIcon
                                        source: "file:assets/icons/x.svg"
                                        sourceSize.width: 20
                                        sourceSize.height: 20
                                        visible: false
                                    }
                                    
                                    MultiEffect {
                                        source: delIcon
                                        anchors.fill: parent
                                        colorization: 1.0
                                        colorizationColor: theme.textColor
                                    }
                                    
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            galleryModel.remove_face(modelData.face_id)
                                            root.peopleList = galleryModel.get_people_in_image(root.currentImagePath)
                                        }
                                    }
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
                                    onClicked: {
                                        peopleView.editingFaceId = -1 // Not editing, adding
                                        personSelectionDialog.title = "Add Person"
                                        personSelectionDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    TagEditDialog {
        id: tagDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 300
        height: 400
        isAddMode: true
        targetPath: root.currentImagePath 
        
        onClosed: {
            root.currentImageDetails = galleryModel.get_image_details(root.currentImagePath)
        }
    }
    
    PersonSelectionDialog {
        id: personSelectionDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 300
        height: 400
        
        onPersonSelected: (personId) => {
            if (peopleView.editingFaceId !== -1) {
                // Formatting: replace existing face person
                galleryModel.reassign_face(peopleView.editingFaceId, personId)
            } else {
                // Add new person to image
                galleryModel.add_person_to_image(root.currentImagePath, personId)
            }
            // Refresh list
            root.peopleList = galleryModel.get_people_in_image(root.currentImagePath)
            personSelectionDialog.close()
        }
    }
}
