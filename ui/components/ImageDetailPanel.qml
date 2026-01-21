import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import ".." // For TagEditDialog
import "detail" // Import the new components

Item {
    id: detailPanelRoot

    property string currentImagePath: ""
    property var currentImageDetails: null
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
        } else {
            currentImageDetails = null
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
                            iconHeight: 25
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
}