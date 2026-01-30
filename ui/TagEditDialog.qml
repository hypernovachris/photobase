import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Dialog {
    id: tagDialog
    property bool isAddMode: false
    modal: true
    
    property var allTags: []
    property var commonTags: []
    property string targetPath: "" // If set, operates on this single file instead of selection
    property var tagsState: ({}) // tag_name -> checked state (true/false)

    // Signals to communicate back
    signal tagsUpdated()

    onOpened: {
        // Load data
        allTags = galleryModel.get_all_tags_list()
        
        if (targetPath !== "") {
            var details = galleryModel.get_image_details(targetPath)
            if (details) {
                commonTags = details.tags
            } else {
                commonTags = []
            }
        } else {
            commonTags = []
        }
        updateTagsState()
    }

    onAccepted: {
        
        for (var i = 0; i < allTags.length; i++) {
            var tag = allTags[i]
            var isChecked = tagsState[tag] === true
            
            if (targetPath !== "") {
                 if (isChecked) {
                     galleryModel.add_tag_to_image_path(targetPath, tag)
                 } else {
                     galleryModel.remove_tag_from_image_path(targetPath, tag)
                 }
            } else {
                if (isChecked) {
                    galleryModel.apply_tag_to_selection(tag)
                } 
            }
        }
        tagsUpdated()
    }

    function updateTagsState() {
        var newState = {}
        for (var i = 0; i < allTags.length; i++) {
            var t = allTags[i]
            // Initially check if it's in common tags
            newState[t] = commonTags.indexOf(t) !== -1
        }
        tagsState = newState
        tagList.model = allTags // Refresh list
    }

    background: Rectangle {
        color: theme.borderColor
        Rectangle {
            anchors.fill: parent
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            anchors.topMargin: 1
            anchors.bottomMargin: 1
            color: theme.backgroundColor
        }
    }

    header: Label {
        text: isAddMode ? "Add Tags" : "Edit Tags"
        font.pixelSize: 14
        color: theme.textColor
        padding: 10
        horizontalAlignment: Text.AlignHCenter
        background: Rectangle {
            color: "transparent"
        }
    }

    ColumnLayout {
        spacing: 10
        anchors.fill: parent

        // New Tag Input
        RowLayout {
            Layout.fillWidth: true
            TextField {
                id: newTagField
                placeholderText: "New Tag Name"
                // change placeholder text color
                placeholderTextColor: theme.secondaryTextColor
                Layout.fillWidth: true
                onAccepted: addBtn.clicked()
                color: theme.textColor
                background: Rectangle {
                    color: theme.secondaryBackgroundColor
                    border.color: theme.borderColor
                }
            }
            StandardButton {
                id: addBtn
                text: "Add"
                enabled: newTagField.text.trim().length > 0
                height: newTagField.height // why won't this work?

                onClicked: {
                    var name = newTagField.text.trim()
                    if (name) {
                        if (galleryModel.add_new_tag(name)) {
                            // Refresh
                            allTags = galleryModel.get_all_tags_list()
                            tagsState[name] = true 
                            tagList.model = allTags
                            newTagField.text = ""
                        }
                    }
                }
            }
        }

        Label {
            text: "Select tags to apply:"
            font.bold: true
            color: theme.textColor
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            height: 200
            clip: true

            ListView {
                id: tagList
                model: allTags
                delegate: CheckBox {
                    text: modelData
                    checked: tagsState[modelData] === true
                    onClicked: {
                        tagsState[modelData] = checked
                    }
                }
            }
        }
    }

    footer: DialogButtonBox {
        background: Rectangle {
            color: "transparent"
        }
        spacing: 10
        StandardButton {
            text: "Cancel"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        StandardButton {
            text: "OK"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
    }
}
