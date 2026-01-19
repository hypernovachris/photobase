import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import ".." // For TagEditDialog, PersonSelectionDialog
import "detail" // Import the new components

Item {
    id: detailPanelRoot

    property string currentImagePath: ""
    property var currentImageDetails: null
    property var peopleList: []
    signal closeRequested()

    property bool isShowingDetails: rightStack.currentIndex === 0

    function resetToDetails() {
        if (rightStack) {
            rightStack.currentIndex = 0
        }
    }
    
    function navigateBack() {
        if (rightStack.currentIndex > 0) {
            rightStack.currentIndex = 0
            return true // Handled
        }
        return false // Not handled
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
                
                ScrollView {
                    anchors.fill: parent
                    contentWidth: availableWidth

                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 20
                        spacing: 15
                    
                    DetailHeader {
                        currentImagePath: detailPanelRoot.currentImagePath
                        onCloseRequested: detailPanelRoot.closeRequested()
                        onOpenFileRequested: galleryModel.open_file(detailPanelRoot.currentImagePath)
                        Layout.fillWidth: true
                    }
                    
                    // Path
                    MetadataRow {
                        layoutDirection: Qt.LeftToRight
                        iconSource: "file:assets/icons/folder.svg"
                        text: detailPanelRoot.currentImagePath ? detailPanelRoot.currentImagePath.substring(0, detailPanelRoot.currentImagePath.lastIndexOf(detailPanelRoot.currentImagePath.split('\\').pop().split('/').pop())).slice(0, -1) : ""
                        isLink: true
                        onLinkActivated: galleryModel.reveal_file(detailPanelRoot.currentImagePath)
                    }
                    
                    // Date
                    MetadataRow {
                         iconSource: "file:assets/icons/calendar-clock.svg"
                         text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.date : ""
                    }

                    // File Size
                    MetadataRow {
                         iconSource: "file:assets/icons/hard-drive.svg"
                         text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.fileSize : ""
                    }

                    // Image Size
                    MetadataRow {
                         iconSource: "file:assets/icons/size_icon.svg"
                         text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.imageSize : ""
                    }

                    // Camera
                    MetadataRow {
                        iconSource: "file:assets/icons/camera.svg"
                        text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.camera : ""
                    }

                    // Lens
                    MetadataRow {
                        iconSource: "file:assets/icons/noun-lens-8154880.svg"
                        text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.lens : ""
                    }
                    
                    // EXIF Data
                    MetadataRow {
                        iconSource: "file:assets/icons/aperture.svg"
                        text: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.exifString : ""
                    }
                    
                    // Tags
                    TagSection {
                        tags: detailPanelRoot.currentImageDetails ? detailPanelRoot.currentImageDetails.tags : []
                        
                        onAddTagRequested: {
                            tagDialog.targetPath = detailPanelRoot.currentImagePath
                            tagDialog.isAddMode = true
                            tagDialog.open()
                        }
                        
                        onRemoveTagRequested: (tagName) => {
                            galleryModel.remove_tag_from_image_path(detailPanelRoot.currentImagePath, tagName)
                            detailPanelRoot.currentImageDetails = galleryModel.get_image_details(detailPanelRoot.currentImagePath)
                        }
                    }
                    
                    // Location (Placeholder)
                    MetadataRow {
                        iconSource: "file:assets/icons/map-pin.svg"
                        text: "Unavailable"
                        isUnavailable: true 
                    }
                    
                    // People
                    PeopleListSection {
                        peopleCount: detailPanelRoot.peopleList ? detailPanelRoot.peopleList.length : 0
                        onClicked: rightStack.currentIndex = 1
                    }

                    }
                }
            }
            
            // View 1: People Edit View
            PeopleEditView {
                id: peopleView
                currentImagePath: detailPanelRoot.currentImagePath
                peopleList: detailPanelRoot.peopleList
                
                onBackRequested: rightStack.currentIndex = 0
                
                onAddPersonRequested: {
                    peopleView.editingFaceId = -1
                    personSelectionDialog.title = "Add Person"
                    personSelectionDialog.open()
                }
                
                onEditPersonRequested: (faceId) => {
                    peopleView.editingFaceId = faceId
                    personSelectionDialog.title = "Replace Person"
                    personSelectionDialog.open()
                }
                
                onRemoveFaceRequested: (faceId) => {
                    galleryModel.remove_face(faceId)
                    detailPanelRoot.peopleList = galleryModel.get_people_in_image(detailPanelRoot.currentImagePath)
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