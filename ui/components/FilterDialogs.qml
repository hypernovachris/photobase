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
    
    function openCameraDialog() { 
        listSelectionDialog.title = "Select Camera Model"
        listSelectionDialog.modelData = galleryModel.get_all_cameras()
        listSelectionDialog.mode = "camera"
        listSelectionDialog.open() 
    }
    function openLensDialog() { 
        listSelectionDialog.title = "Select Lens Model"
        listSelectionDialog.modelData = galleryModel.get_all_lenses()
        listSelectionDialog.mode = "lens"
        listSelectionDialog.open() 
    }

    function openFolderDialog() { stringDialog.mode = "folder"; stringDialog.title = "Folder Name"; stringDialog.open() }
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
        width: mode === "between" ? 650 : 350
        height: 450
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        property string mode: "before"
        // Return YYYY-MM-DD string(s)
        
        RowLayout {
            anchors.fill: parent
            spacing: 20
            
            ColumnLayout {
                Layout.fillWidth: true
                Label { 
                    text: dateDialog.mode === "between" ? "Start Date:" : "Date:" 
                    font.bold: true
                }
                
                DatePicker {
                    id: datePicker1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onDateSelected: (d) => { date1String.text = Qt.formatDate(d, "yyyy-MM-dd") }
                }
                TextField {
                    id: date1String
                    text: Qt.formatDate(new Date(), "yyyy-MM-dd")
                    Layout.fillWidth: true
                    readOnly: true
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            
            ColumnLayout {
                visible: dateDialog.mode === "between"
                Layout.fillWidth: true
                
                Label { 
                    text: "End Date:" 
                    font.bold: true
                }
                
                DatePicker {
                    id: datePicker2
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onDateSelected: (d) => { date2String.text = Qt.formatDate(d, "yyyy-MM-dd") }
                }
                TextField {
                    id: date2String
                    text: Qt.formatDate(new Date(), "yyyy-MM-dd")
                    Layout.fillWidth: true
                    readOnly: true
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
        
        onOpened: {
            // Reset to today
            var today = new Date()
            datePicker1.setDate(today)
            date1String.text = Qt.formatDate(today, "yyyy-MM-dd")
            
            if (mode === "between") {
                datePicker2.setDate(today)
                date2String.text = Qt.formatDate(today, "yyyy-MM-dd")
            }
        }

        onAccepted: {
            var val = date1String.text
            if (mode === "between") {
                val = { start: date1String.text, end: date2String.text }
            }
            root.filterAdded(mode, val)
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

    // --- Generic List Selection Dialog (Camera/Lens) ---
    Dialog {
        id: listSelectionDialog
        title: "Select Item"
        anchors.centerIn: Overlay.overlay
        width: 300
        height: 400
        modal: true
        standardButtons: Dialog.Cancel
        
        property var modelData: []
        property string mode: ""

        ListView {
            anchors.fill: parent
            model: listSelectionDialog.modelData
            clip: true
            
            delegate: ItemDelegate {
                text: modelData
                width: ListView.view.width
                onClicked: {
                    root.filterAdded(listSelectionDialog.mode, modelData)
                    listSelectionDialog.close()
                }
            }
        }
    }

    // --- Generic String Dialog (Folder, Ext, Filename) ---
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
