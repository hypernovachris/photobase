import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import ".." // For TagEditDialog, PersonSelectionDialog

Item {
    id: detailPanelRoot

    property string currentImagePath: ""
    property var currentImageDetails: null
    property var peopleList: []
    signal closeRequested()

    function resetToDetails() {
        if (rightStack) {
            rightStack.currentIndex = 0
        }
    }

    onCurrentImagePathChanged: {
        if (currentImagePath) {
            currentImageDetails = galleryModel.get_image_details(currentImagePath)
            peopleList = galleryModel.get_people_in_image(currentImagePath)
        } else {
            currentImageDetails = null
            peopleList = []
        }
    }

    Rectangle {
        anchors.fill: parent
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
                    
                    // Header: Filename + Extension +Close
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        // 1. NESTED LAYOUT (Holds Name + Ext + Spacer)
                        RowLayout {
                            spacing: 0
                            Layout.fillWidth: true 

                            // A. FILENAME
                            Text {
                                id: filenameText
                                text: detailPanelRoot.currentImagePath ? detailPanelRoot.currentImagePath.split('\\').pop().split('/').pop().split('.')[0] : ""
                                font.pixelSize: 24
                                font.bold: true
                                color: theme.textColor
                                
                                elide: Text.ElideRight
                                Layout.alignment: Qt.AlignBaseline
                                
                                Layout.fillWidth: true             // Enable dynamic sizing
                                Layout.minimumWidth: 0             // Allow shrinking (eliding)
                                Layout.maximumWidth: implicitWidth // Prevent growing (keeps extension attached)

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: galleryModel.open_file(detailPanelRoot.currentImagePath)
                                }
                            }

                            // B. EXTENSION
                            Text {
                                text: detailPanelRoot.currentImagePath ? "." + detailPanelRoot.currentImagePath.split('\\').pop().split('/').pop().split('.')[1].toUpperCase() : ""
                                font.pixelSize: 16
                                font.bold: true
                                color: theme.textColor
                                Layout.alignment: Qt.AlignBaseline
                                
                                // Default layout behavior is fine here (fixed width)

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: galleryModel.open_file(detailPanelRoot.currentImagePath)
                                }
                            }

                            // C. INTERNAL SPACER
                            // This eats all the empty space on the right, pushing the texts to the left.
                            Item {
                                Layout.fillWidth: true 
                            }
                        }

                        // 2. CLOSE BUTTON
                        Item {
                            width: 30
                            height: 30
                            Layout.alignment: Qt.AlignVCenter

                            IconButton {
                                anchors.fill: parent
                                source: "file:assets/icons/x.svg"
                                iconSize: 30
                                onClicked: detailPanelRoot.closeRequested()
                            }
                        }
                    }
                    
                    // Path
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignLeft
                        spacing: 10
                        
                        // Folder icon
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/folder.svg"
                            iconSize: 20
                        }
                        
                        Text {
                            text: detailPanelRoot.currentImagePath ? detailPanelRoot.currentImagePath.substring(0, detailPanelRoot.currentImagePath.lastIndexOf(detailPanelRoot.currentImagePath.split('\\').pop().split('/').pop())).slice(0, -1) : ""
                            font.pixelSize: 14
                            color: theme.textColor
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                            
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    galleryModel.reveal_file(detailPanelRoot.currentImagePath)
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
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/clock.svg"
                            iconSize: 20
                        }
                        Text {
                            text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.date : ""
                            font.pixelSize: 14
                            color: theme.textColor
                        }
                    }

                    // Camera
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignLeft
                        spacing: 10
                        // Camera icon
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/camera.svg"
                            iconSize: 20
                        }
                        Text {
                            text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.camera : "Unavailable"
                            font.italic: (text === "Unavailable")
                            font.pixelSize: 14
                            color: theme.textColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            opacity: (text === "Unavailable") ? 0.7 : 1.0
                        }
                    }

                    // Lens
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignLeft
                        spacing: 10
                        // Lens icon
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/noun-lens-8154880.svg"
                            iconSize: 20
                        }
                        Text {
                            text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.lens : "Unavailable"
                            font.italic: (text === "Unavailable")
                            font.pixelSize: 14
                            color: theme.textColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            opacity: (text === "Unavailable") ? 0.7 : 1.0
                        }
                    }
                    
                    // EXIF Data
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignLeft
                        spacing: 10
                        // Aperture icon
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/aperture.svg"
                            iconSize: 20
                        }
                        Text {
                            text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.exifString : "Unavailable"
                            font.italic: (text === "Unavailable")
                            font.pixelSize: 14
                            color: theme.textColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            opacity: (text === "Unavailable") ? 0.7 : 1.0
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
                            IconButton {
                                anchors.centerIn: parent
                                clickable: false
                                source: "file:assets/icons/tag.svg"
                                iconSize: 20
                            }
                        }

                        // Tags
                        Repeater {
                            visible: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.tags.length > 0 : false
                            model: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.tags : []
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
                                    
                                        IconButton {
                                            width: 16
                                            height: 16
                                            iconSize: 16
                                            anchors.verticalCenter: parent.verticalCenter
                                            source: "file:assets/icons/x.svg"
                                            color: theme.buttonTextColor
                                            onClicked: {
                                                galleryModel.remove_tag_from_image_path(detailPanelRoot.currentImagePath, modelData)
                                                detailPanelRoot.currentImageDetails = galleryModel.get_image_details(detailPanelRoot.currentImagePath)
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
                                
                                IconButton {
                                    anchors.fill: parent
                                    source: "file:assets/icons/plus.svg"
                                    color: theme.textColor
                                    onClicked: {
                                        tagDialog.targetPath = detailPanelRoot.currentImagePath
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
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/map-pin.svg"
                            iconSize: 20
                        }
                        Text {
                            text: "Unavailable"
                            font.italic: true
                            color: theme.textColor
                            opacity: 0.7
                            font.pixelSize: 14
                        }
                    }
                    
                    // People
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignLeft
                        spacing: 10

                        // People icon
                        IconButton {
                            clickable: false
                            source: "file:assets/icons/scan-face.svg"
                            iconSize: 20
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
                                    text: (detailPanelRoot.peopleList ? detailPanelRoot.peopleList.length : "None") + " detected"
                                    color: theme.textColor
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 14
                                }

                                // Link icon
                                IconButton {
                                    clickable: false
                                    source: "file:assets/icons/external-link-3px.svg"
                                    iconSize: 16
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
                                text: detailPanelRoot.currentImagePath ? (detailPanelRoot.currentImagePath.split('\\').pop().split('/').pop()).toUpperCase() + "/" : ""
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
                            onClicked: rightStack.currentIndex = 0
                        }
                    }
                    
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: detailPanelRoot.peopleList
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
                                    source: (!faceWrapper.isManual && detailPanelRoot.currentImagePath) ? galleryModel.get_image_url(detailPanelRoot.currentImagePath) : ""
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
                                onClicked: {
                                    peopleView.editingFaceId = modelData.face_id
                                    personSelectionDialog.title = "Replace Person"
                                    personSelectionDialog.open()
                                }
                            }

                            IconButton {
                                width: 20
                                height: 20
                                source: "file:assets/icons/x.svg"
                                onClicked: {
                                    galleryModel.remove_face(modelData.face_id)
                                    detailPanelRoot.peopleList = galleryModel.get_people_in_image(detailPanelRoot.currentImagePath)
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
    TagEditDialog {
        id: tagDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 300
        height: 400
        isAddMode: true
        targetPath: detailPanelRoot.currentImagePath 
        
        onClosed: {
            detailPanelRoot.currentImageDetails = galleryModel.get_image_details(detailPanelRoot.currentImagePath)
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
                galleryModel.add_person_to_image(detailPanelRoot.currentImagePath, personId)
            }
            // Refresh list
            detailPanelRoot.peopleList = galleryModel.get_people_in_image(detailPanelRoot.currentImagePath)
            personSelectionDialog.close()
        }
    }
}