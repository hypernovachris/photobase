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
    function openDateBetweenDialog() { 
        var today = new Date()
        betweenDialog.startDate = today
        betweenDialog.endDate = today
        betweenDialog.open() 
    }
    
    function openTagDialog() { 
        listSelectionDialog.modelData = galleryModel.get_all_tags_list()
        listSelectionDialog.mode = "tag"
        listSelectionDialog.open()
    }
    
    function openCameraDialog() { 
        listSelectionDialog.modelData = galleryModel.get_all_cameras()
        listSelectionDialog.mode = "camera"
        listSelectionDialog.open() 
    }
    function openLensDialog() { 
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
        anchors.centerIn: Overlay.overlay
        width: 350
        height: 450
        modal: true

        property string mode: "before"
        property var onDatePickedCallback: null // If set, this callback is called with the date instead of filterAdded
        property string customTitle: ""
        property var pendingDate: null // Date to show when opened

        background: Rectangle {
            color: theme.borderColor
            radius: 10
            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 1
                anchors.rightMargin: 1
                anchors.topMargin: 1
                anchors.bottomMargin: 1
                color: theme.backgroundColor
                radius: 9
            }
        }

        header: Label {
            text: {
                if (dateDialog.customTitle !== "") return dateDialog.customTitle
                if (dateDialog.mode === "before") return "Before Date"
                return "Since Date"
            }
            color: theme.textColor
            font.bold: true
            padding: 10
            horizontalAlignment: Text.AlignHCenter
            background: Rectangle {
                color: "transparent"
            }
        }

                RowLayout {
            anchors.fill: parent
            spacing: 20
            
            ColumnLayout {
                Layout.fillWidth: true                
                DatePicker {
                    id: datePicker1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onDateSelected: (d) => { dateString.text = Qt.formatDate(d, "yyyy-MM-dd") }
                }
                Label {
                    id: dateString
                    text: Qt.formatDate(new Date(), "yyyy-MM-dd")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    visible: false
                }
            }
        }
        
        onOpened: {
            var d = new Date()
            if (dateDialog.pendingDate) {
                d = dateDialog.pendingDate
            }
            datePicker1.setDate(d)
            dateString.text = Qt.formatDate(d, "yyyy-MM-dd")
            dateDialog.pendingDate = null
        }

        onAccepted: {
            var val = dateString.text
            if (dateDialog.onDatePickedCallback) {
                // Parse the date string back to a Date object or pass the string depending on needs.
                // The datePicker1.selectedDate holds the Date object.
                dateDialog.onDatePickedCallback(datePicker1.selectedDate)
            } else {
                root.filterAdded(mode, val)
            }
        }
        
        onClosed: {
            // Reset callback and title when closed to avoid side effects
            dateDialog.onDatePickedCallback = null
            dateDialog.customTitle = ""
        }

        footer: DialogButtonBox {
            background: Rectangle {
                color: "transparent"
            }
            spacing: 10
            Button {
                text: "Cancel"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
            Button {
                text: "OK"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
        }

    }

    // --- Between Dates Dialog ---
    Dialog {
        id: betweenDialog
        anchors.centerIn: Overlay.overlay
        width: 300
        height: 250 // Compact height
        modal: true

        property date startDate: new Date()
        property date endDate: new Date()

        background: Rectangle {
            color: theme.borderColor
            radius: 10
            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 1
                anchors.rightMargin: 1
                anchors.topMargin: 1
                anchors.bottomMargin: 1
                color: theme.backgroundColor
                radius: 9
            }
        }

        header: Label {
            text: "Between Dates"
            color: theme.textColor
            font.bold: true
            padding: 10
            horizontalAlignment: Text.AlignHCenter
            background: Rectangle {
                color: "transparent"
            }
        }

        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width * 0.8
            spacing: 20
            
            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: "Start date:"
                    color: theme.textColor
                    Layout.preferredWidth: 80
                }
                Button {
                    text: Qt.formatDate(betweenDialog.startDate, "yyyy-MM-dd")
                    Layout.fillWidth: true
                    palette.buttonText: theme.textColor
                    background: Rectangle {
                        color: theme.buttonColor
                        radius: 5
                    }
                    onClicked: {
                        dateDialog.customTitle = "Select Start Date"
                        dateDialog.pendingDate = betweenDialog.startDate
                        dateDialog.onDatePickedCallback = function(d) {
                            betweenDialog.startDate = d
                        }
                        dateDialog.open()
                    }
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: "End date:"
                    color: theme.textColor
                    Layout.preferredWidth: 80
                }
                Button {
                    text: Qt.formatDate(betweenDialog.endDate, "yyyy-MM-dd")
                    Layout.fillWidth: true
                    palette.buttonText: theme.textColor
                    background: Rectangle {
                        color: theme.buttonColor
                        radius: 5
                    }
                    onClicked: {
                        dateDialog.customTitle = "Select End Date"
                        dateDialog.pendingDate = betweenDialog.endDate
                        dateDialog.onDatePickedCallback = function(d) {
                            betweenDialog.endDate = d
                        }
                        dateDialog.open()
                    }
                }
            }
        }

        footer: DialogButtonBox {
            background: Rectangle {
                color: "transparent"
            }
            spacing: 10
            Button {
                text: "Cancel"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
            Button {
                text: "OK"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
            onAccepted: {
                var startStr = Qt.formatDate(betweenDialog.startDate, "yyyy-MM-dd")
                var endStr = Qt.formatDate(betweenDialog.endDate, "yyyy-MM-dd")
                root.filterAdded("between", {start: startStr, end: endStr})
            }
        }
    }

    // --- Generic List Selection Dialog (Camera/Lens) ---
    Dialog {
        id: listSelectionDialog
        anchors.centerIn: Overlay.overlay
        width: 300
        height: 400
        modal: true

        property var modelData: []
        property string mode: ""

        background: Rectangle {
            color: theme.borderColor
            radius: 10
            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 1
                anchors.rightMargin: 1
                anchors.topMargin: 1
                anchors.bottomMargin: 1
                color: theme.backgroundColor
                radius: 9
            }
        }

        header: Label {
            text: "Select " + listSelectionDialog.mode.charAt(0).toUpperCase() + listSelectionDialog.mode.slice(1) 
            color: theme.textColor
            font.pixelSize: 14
            padding: 10
            horizontalAlignment: Text.AlignHCenter
            background: Rectangle {
                color: "transparent"
            }
        }

        footer: DialogButtonBox {
            background: Rectangle {
                color: "transparent"
            }
            Button {
                text: "Cancel"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
            onRejected: listSelectionDialog.close()
        }
        
        ListView {
            id: listSelectionListView
            anchors.fill: parent
            model: listSelectionDialog.modelData
            clip: true
            spacing: 5
            
            delegate: ItemDelegate {
                text: modelData
                palette.text: theme.textColor
                width: ListView.view.width
                onClicked: {
                    root.filterAdded(listSelectionDialog.mode, modelData)
                    listSelectionDialog.close()
                }
                // background rectangle
                background: Rectangle {
                    anchors.fill: parent
                    color: theme.buttonColor
                    radius: 5
                }
            }
        }
    }

    // --- Generic String Dialog (Folder, Ext, Filename) ---
    Dialog {
        id: stringDialog
        anchors.centerIn: Overlay.overlay
        width: 300
        modal: true

        property string mode: ""

        background: Rectangle {
            color: theme.borderColor
            radius: 10
            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 1
                anchors.rightMargin: 1
                anchors.topMargin: 1
                anchors.bottomMargin: 1
                color: theme.backgroundColor
                radius: 9
            }
        }

        header: Label {
            text: "Enter Value"
            color: theme.textColor
            font.pixelSize: 14
            padding: 10
            horizontalAlignment: Text.AlignHCenter
            background: Rectangle {
                color: "transparent"
            }
        }

        footer: DialogButtonBox {
            background: Rectangle {
                color: "transparent"
            }
            spacing: 10
            Button {
                text: "Cancel"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
            Button {
                text: "OK"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
                palette.buttonText: theme.textColor
                background: Rectangle {
                    color: theme.buttonColor
                    radius: 5
                }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            TextField {
                id: stringInput
                Layout.fillWidth: true
                focus: true
                palette.text: theme.textColor
                palette.placeholderText: theme.placeholderTextColor
                background: Rectangle {
                    color: theme.textFieldColor
                    border.color: theme.borderColor
                    border.width: 1
                }
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
