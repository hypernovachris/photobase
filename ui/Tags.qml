import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        Label {
            text: "Tags"
            color: theme.textColor
            font.bold: true
            font.pixelSize: 32
        }

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Flow {
                width: scrollView.availableWidth
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
                                                source = ""
                                                source = Qt.binding(function() { return Qt.resolvedUrl(thumbPath) })
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
                                        // Optional: Switch tab if we could.
                                    }
                                }
                            }
                            
                            Column {
                                width: 140
                                spacing: 2
                                
                                Text {
                                    text: tagData.name
                                    color: theme.textColor
                                    font.bold: true
                                    font.pixelSize: 16
                                    elide: Text.ElideRight
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
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
    
    // Auto-refresh logic (Needs to re-trigger binding or model update)
    // Repeater model binding should handle it if 'get_all_tags_model' was a property or signal.
    // Since it's a function, we need to manually call it.
    
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
