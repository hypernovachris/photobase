import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: root

    // --- State ---
    
    ListModel {
        id: activeFiltersModel
    }

    property bool isNegatedMode: false

    function addFilter(type, value) {
        // Construct a human readable label
        var label = type + ": " + value
        var storedValue = value // Keep original for display/logic if needed, but ListModel needs consistent type?
        
        if (type === "tag") label = "Tag: " + value
        
        if (type === "date_between" || type === "between") {
             // value is {start: "...", end: "..."}
             label = "Between " + value.start + " and " + value.end
             storedValue = JSON.stringify(value)
        }
        
        if (type === "before") label = "Before " + value
        if (type === "since") label = "Since " + value
        if (type === "camera") label = "Camera: " + value
        if (type === "lens") label = "Lens: " + value
        if (type === "folder") label = "Folder: " + value
        if (type === "extension") label = "Ext: " + value
        if (type === "filename") label = "Filename: " + value

        activeFiltersModel.append({
            "type": type,
            "value": String(storedValue), // Force string
            "negated": isNegatedMode,
            "label": (isNegatedMode ? "NOT " : "") + label
        })
    }

    function performSearch() {
        var filters = []
        for(var i = 0; i < activeFiltersModel.count; i++) {
            var item = activeFiltersModel.get(i)
            filters.push({
                "type": item.type,
                "value": item.value,
                "negated": item.negated
            })
        }
        // Call backend
        if (galleryModel.search) {
             galleryModel.search(filters)
        } else {
             console.warn("galleryModel.search not implemented yet")
        }
    }

    // --- Dialogs ---

    FilterDialogs { 
        id: filterDialogs 
        onFilterAdded: (type, value) => {
             root.addFilter(type, value)
        }
    }

    // --- Main Layout ---
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 1. Search Bar Area
        Rectangle {
            Layout.fillWidth: true
            height: 60
            color: theme.backgroundColor

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 0
                Item {
                    width: 10
                }
                // Search Bar Input (Visual representation of filters)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: theme.backgroundColor
                    border.color: theme.borderColor
                    topLeftRadius: 4
                    bottomLeftRadius: 4
                    anchors.margins: 10
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 5
                        spacing: 5
                        
                        // Placeholder
                        Text {
                            visible: activeFiltersModel.count === 0
                            text: "Start by adding a filter..."
                            color: theme.secondaryTextColor
                            font.italic: true
                            Layout.alignment: Qt.AlignVCenter
                            leftPadding: 5
                        }

                        // Filter Chips
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            orientation: ListView.Horizontal
                            spacing: 5
                            model: activeFiltersModel
                            clip: true
                            
                            delegate: Rectangle {
                                height: 30
                                width: chipRow.implicitWidth + 20
                                color: theme.buttonColor
                                radius: 15
                                
                                RowLayout {
                                    id: chipRow
                                    anchors.centerIn: parent
                                    spacing: 5
                                    Text {
                                        text: model.label
                                        color: theme.textColor
                                        font.pixelSize: 12
                                    }
                                    IconButton {
                                        source: "file:assets/icons/x.svg"
                                        onClicked: {
                                            activeFiltersModel.remove(model.index)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Search Button (Execute)
                Button {
                    enabled: activeFiltersModel.count > 0
                    Layout.preferredWidth: 80
                    Layout.fillHeight: true
                    onClicked: performSearch()
                    IconButton {
                        source: "file:assets/icons/search.svg"
                        clickable: false
                        // center in button
                        anchors.centerIn: parent
                    }
                    background: Rectangle {
                        color: theme.buttonColor
                        topRightRadius: 4
                        bottomRightRadius: 4
                    }
                }
                Item {
                    width: 10
                }
            }
        }
        
        // 2. Filter Controls Area
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: filterGrid.implicitHeight + 40
            color: theme.backgroundColor
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Filters"
                        font.pixelSize: 24
                        color: theme.textColor
                        Layout.fillWidth: true
                    }
                    
                    Button {
                        text: "Toggle negative filters"
                        checkable: true
                        checked: isNegatedMode
                        onCheckedChanged: isNegatedMode = checked
                        
                        background: Rectangle {
                           color: parent.checked ? "red" : theme.buttonColor
                           border.color: theme.borderColor
                           radius: 4
                        }
                        contentItem: Text {
                            text: parent.text
                            color: parent.checked ? "white" : theme.textColor
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: theme.borderColor
                }
                
                Flow {
                    id: filterGrid
                    Layout.fillWidth: true
                    spacing: 10
                    
                    // Button Factory
                    component FilterButton: Button {
                        // width: implicitWidth  // Let it size to content
                        height: 30
                        leftPadding: 15
                        rightPadding: 15
                        
                        background: Rectangle {
                            color: theme.buttonColor
                            radius: 15
                        }
                        contentItem: Text {
                            text: parent.text
                            color: theme.textColor
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    FilterButton { text: "Before date"; onClicked: filterDialogs.openDateBeforeDialog() }
                    FilterButton { text: "Since date"; onClicked: filterDialogs.openDateSinceDialog() }
                    FilterButton { text: "Between dates"; onClicked: filterDialogs.openDateBetweenDialog() }
                    FilterButton { text: "Has tag"; onClicked: filterDialogs.openTagDialog() }

                    FilterButton { text: "Taken with camera"; onClicked: filterDialogs.openCameraDialog() }
                    FilterButton { text: "Taken with lens"; onClicked: filterDialogs.openLensDialog() }
            
                    FilterButton { text: "In folder"; onClicked: filterDialogs.openFolderDialog() }
                    FilterButton { text: "Has file extension"; onClicked: filterDialogs.openExtensionDialog() }
                    FilterButton { text: "Filename starts with"; onClicked: filterDialogs.openFilenameDialog() }
                }
            }
        }
        
        // Spacer for remaining height
        Item { 
            Layout.fillWidth: true 
            Layout.fillHeight: true 
        }
    }
}
