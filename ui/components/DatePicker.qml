import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    
    property date selectedDate: new Date()
    property alias currentMonth: grid.month
    property alias currentYear: grid.year
    
    signal dateSelected(date date)
    
    implicitWidth: 300
    implicitHeight: 320
    
    function setDate(d) {
        if (d instanceof Date && !isNaN(d.getTime())) {
            selectedDate = d
            grid.month = d.getMonth()
            grid.year = d.getFullYear()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        
        // Header (Month + Year Navigation)
        RowLayout {
            Layout.fillWidth: true
            spacing: 0
            
            // Month Navigation
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 0 // Force equal 50% split (minus spacing)
                spacing: 5
                
                Button {
                    Layout.preferredWidth: 30
                    IconButton {
                        source: "file:assets/icons/arrow-left.svg"
                        clickable: false
                        color: "black"
                        anchors.centerIn: parent
                    }
                    onClicked: {
                        if (grid.month === 0) {
                            grid.month = 11
                            grid.year -= 1
                        } else {
                            grid.month -= 1
                        }
                    }
                }
                
                Label {
                    text: Qt.formatDate(new Date(grid.year, grid.month, 1), "MMMM")
                    font.bold: true
                    font.pixelSize: 14
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                }
                
                Button {
                    Layout.preferredWidth: 30
                    IconButton {
                        source: "file:assets/icons/arrow-right.svg"
                        clickable: false
                        color: "black"
                        anchors.centerIn: parent
                    }
                    onClicked: {
                        if (grid.month === 11) {
                            grid.month = 0
                            grid.year += 1
                        } else {
                            grid.month += 1
                        }
                    }
                }
            }
            
            // Spacer
            Item { width: 10 }
            
            // Year Navigation
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 0 // Force equal 50% split (minus spacing)
                spacing: 5
                
                Button {
                    Layout.preferredWidth: 30
                    IconButton {
                        source: "file:assets/icons/arrow-left.svg"
                        clickable: false
                        color: "black"
                        anchors.centerIn: parent
                    }
                    onClicked: grid.year -= 1
                }
                
                Label {
                    text: grid.year
                    font.bold: true
                    font.pixelSize: 14
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                }
                
                Button {
                    Layout.preferredWidth: 30
                    IconButton {
                        source: "file:assets/icons/arrow-right.svg"
                        clickable: false
                        color: "black"
                        anchors.centerIn: parent
                    }
                    onClicked: grid.year += 1
                }
            }
        }
        
        // Days of Week
        DayOfWeekRow {
            Layout.fillWidth: true
            delegate: Text {
                text: model.shortName
                horizontalAlignment: Text.AlignHCenter
                font.bold: true
            }
        }
        
        // Month Grid
        MonthGrid {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            month: new Date().getMonth()
            year: new Date().getFullYear()
            
            delegate: Rectangle {
                opacity: model.month === grid.month ? 1 : 0.3
                color: {
                    var d = model.date
                    var s = root.selectedDate
                    if (d.getDate() === s.getDate() && 
                        d.getMonth() === s.getMonth() && 
                        d.getFullYear() === s.getFullYear()) {
                        return "#0077EE" // Highlight
                    }
                    return "transparent"
                }
                radius: 4
                
                Text {
                    anchors.centerIn: parent
                    text: model.day
                    color: {
                         var d = model.date
                         var s = root.selectedDate
                         if (d.getDate() === s.getDate() && 
                             d.getMonth() === s.getMonth() && 
                             d.getFullYear() === s.getFullYear()) {
                             return "white"
                         }
                         return "black"
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        root.selectedDate = model.date
                        root.dateSelected(model.date)
                    }
                }
            }
        }
    }
}
