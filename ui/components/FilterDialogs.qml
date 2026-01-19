import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    // Signal emitted when a filter is confirmed
    // value can be a string, object, etc.
    signal filterAdded(string type, var value)

    property bool isNegated: false

    function openDateBeforeDialog() { dateDialog.mode = "before"; dateDialog.open() }
    function openDateSinceDialog() { dateDialog.mode = "since"; dateDialog.open() }
    function openDateBetweenDialog() { dateDialog.mode = "between"; dateDialog.open() }
    
    function openTagDialog() { tagDialog.open() }
    function openPersonDialog() { personDialog.open() }
    
    function openCameraDialog() { stringDialog.mode = "camera"; stringDialog.title = "Camera Model"; stringDialog.open() }
    function openLensDialog() { stringDialog.mode = "lens"; stringDialog.title = "Lens Model"; stringDialog.open() }
    function openFolderDialog() { stringDialog.mode = "folder"; stringDialog.title = "Folder Path"; stringDialog.open() }
    function openExtensionDialog() { stringDialog.mode = "extension"; stringDialog.title = "File Extension"; stringDialog.open() }
    function openFilenameDialog() { stringDialog.mode = "filename"; stringDialog.title = "Filename Starts With"; stringDialog.open() }

    // --- Date Dialog ---
    Dialog {
        id: dateDialog
        title: {
            if (mode === "before") return "Before Date"
            if (mode === "since") return "Since Date"
            return "Between Dates"
        }
        anchors.centerIn: Overlay.overlay
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        property string mode: "before"
        // Simple text input for MVP dates (YYYY-MM-DD)
        // Ideally use a Calendar picker, but text is easier for now.
        
        ColumnLayout {
            Label { text: "Date (YYYY-MM-DD):" }
            TextField { 
                id: dateInput1 
                placeholderText: "2023-01-01"
                text: ""
            }
            
            Label { 
                text: "And:" 
                visible: dateDialog.mode === "between"
            }
            TextField { 
                id: dateInput2
                visible: dateDialog.mode === "between"
                placeholderText: "2023-12-31"
            }
        }

        onAccepted: {
            var val = dateInput1.text
            if (mode === "between") {
                val = { start: dateInput1.text, end: dateInput2.text }
            }
            root.filterAdded(mode, val)
            dateInput1.text = ""
            dateInput2.text = ""
        }
    }

    // --- Tag Dialog ---
    Dialog {
        id: tagDialog
        title: "Select Tag"
        anchors.centerIn: Overlay.overlay
        width: 300
        height: 400
        modal: true
        standardButtons: Dialog.Cancel

        ListView {
            id: tagListView
            anchors.fill: parent
            model: galleryModel.get_all_tags_list() // Returns strings
            clip: true
            
            delegate: ItemDelegate {
                text: modelData
                width: parent.width
                onClicked: {
                    root.filterAdded("tag", modelData)
                    tagDialog.close()
                }
            }
        }
    }

    // --- Person Dialog ---
    Dialog {
        id: personDialog
        title: "Select Person"
        anchors.centerIn: Overlay.overlay
        width: 300
        height: 400
        modal: true
        standardButtons: Dialog.Cancel

        ListView {
            id: personListView
            anchors.fill: parent
            model: galleryModel.get_people_model() // Returns objects
            clip: true
            
            delegate: ItemDelegate {
                text: modelData.name
                width: parent.width
                onClicked: {
                    root.filterAdded("person", modelData.id) // Use ID for person
                    personDialog.close()
                }
            }
        }
    }

    // --- Generic String Dialog ---
    Dialog {
        id: stringDialog
        title: "Enter Value"
        anchors.centerIn: Overlay.overlay
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        property string mode: ""

        ColumnLayout {
            TextField { 
                id: stringInput
                Layout.fillWidth: true
                focus: true
            }
        }
        
        onOpened: {
            stringInput.text = ""
            stringInput.forceActiveFocus()
        }

        onAccepted: {
            root.filterAdded(mode, stringInput.text)
        }
    }
}
