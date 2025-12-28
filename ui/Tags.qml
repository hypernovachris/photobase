import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        // anchors.margins: 20
        // spacing: 20

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true


            Column {
                x: 20
                y: 20
                width: scrollView.availableWidth - 40
                spacing: 20
                    
                Label {
                    text: "Tags"
                    color: theme.textColor
                    font.bold: true
                    font.pixelSize: 32
                }
                
                Flow {
                    width: parent.width
                    spacing: 20
                    padding: 10
                    
                    Repeater {
                        model: tagsModel
                        
                        delegate: Item {
                            width: 160
                            height: 200
                            
                            property var tagData: modelData
                            
                            Column {
                                anchors.centerIn: parent
                                spacing: 8
                                
                                // Card
                                Rectangle {
                                    width: 140
                                    height: 140
                                    color: theme.buttonColor
                                    border.color: hoverArea.containsMouse ? theme.highlightColor : theme.borderColor
                                    border.width: hoverArea.containsMouse ? 2 : 1
                                    
                                    Image {
                                        id: tagImage
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        source: tagData.thumbnail || "" 
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                        
                                        onStatusChanged: {
                                            if (status === Image.Error && tagData.coverPath) {
                                                thumbnailGenerator.request_thumbnail(tagData.coverPath)
                                            }
                                        }
                                        
                                        Connections {
                                            target: thumbnailGenerator
                                            function onThumbnailReady(filePath, thumbPath) {
                                                if (tagData.coverPath === filePath) {
                                                    tagImage.source = ""
                                                    tagImage.source = Qt.binding(function() { return Qt.resolvedUrl(thumbPath) })
                                                }
                                            }
                                        }
                                    }
                                    
                                    MouseArea {
                                        id: hoverArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            galleryModel.set_tag_filter(tagData.name)
                                        }
                                    }
                                }
                                
                                Column {
                                    width: 140
                                    spacing: 2
                                    
                                    TextField {
                                        text: tagData.name
                                        placeholderText: "Tag name"
                                        color: theme.textColor
                                        background: Rectangle { color: "transparent" }
                                        horizontalAlignment: TextInput.AlignHCenter
                                        font.bold: true
                                        font.pixelSize: 16
                                        width: parent.width
                                        
                                        onEditingFinished: {
                                            if (text !== tagData.name) {
                                                galleryModel.rename_tag(tagData.id, text)
                                            }
                                            focus = false
                                        }
                                    }
                                    
                                    Text {
                                        text: tagData.count + " Photos"
                                        font.pixelSize: 12
                                        color: theme.secondaryTextColor
                                        width: parent.width
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    property var tagsModel: []
    
    onVisibleChanged: {
        if (visible) {
            refreshTags()
        }
    }
    
    Connections {
        target: galleryModel
        function onTagsChanged() {
            refreshTags()
        }
    }
    
    function refreshTags() {
        tagsModel = galleryModel.get_all_tags_model()
    }
    
    Component.onCompleted: refreshTags()
}
