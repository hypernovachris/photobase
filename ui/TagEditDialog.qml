import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: tagDialog
    property bool isAddMode: false
    title: isAddMode ? "Add Tag" : "Edit Tags"
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    
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
            commonTags = isAddMode ? [] : galleryModel.get_common_tags()
        }
        updateTagsState()
    }

    onAccepted: {
        // Apply changes
        // For each tag that is checked -> add
        // For each tag that is unchecked -> remove
        // Optimization: Only if changed from original state? 
        // For now, simpler to just apply/remove based on final state could be redundant but safe.
        // Actually, better:
        // iterate allTags.
        // if checked and NOT in commonTags -> add
        // if unchecked and IN commonTags -> remove
        // Wait, what if it was mixed? (Not in common, but on some). 
        // If user Checks it -> Add to ALL properly.
        // If user Unchecks it -> Remove from ALL properly.
        // So simple Logic:
        // Checked -> apply_tag_to_selection
        // Unchecked -> remove_tag_from_selection
        
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
                } else if (!isAddMode) {
                    galleryModel.remove_tag_from_selection(tag)
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

    ColumnLayout {
        spacing: 10
        anchors.fill: parent

        // New Tag Input
        RowLayout {
            Layout.fillWidth: true
            TextField {
                id: newTagField
                placeholderText: "New Tag Name"
                Layout.fillWidth: true
                onAccepted: addBtn.clicked()
            }
            Button {
                id: addBtn
                text: "Add"
                enabled: newTagField.text.trim().length > 0
                onClicked: {
                    var name = newTagField.text.trim()
                    if (name) {
                        if (galleryModel.add_new_tag(name)) {
                            // Refresh
                            allTags = galleryModel.get_all_tags_list()
                            // Also mark it as checked? Usually yes if I created it I want to apply it.
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
}
