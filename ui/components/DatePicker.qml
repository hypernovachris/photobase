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
            IconButton {
                Layout.preferredWidth: 30
                source: "file:assets/icons/arrow-left.svg"
                Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
                onClicked: {
                    if (grid.month === 0) {
                        grid.month = 11
                        grid.year -= 1
                    } else {
                        grid.month -= 1
                    }
                }
            }
            // Month Navigation
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 0 // Force equal 50% split (minus spacing)
                spacing: 5
                StyledComboBox {
                    Layout.fillWidth: true
                    model: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                    currentIndex: grid.month
                    font.bold: true
                    font.pixelSize: 16
                    onActivated: (index) => grid.month = index
                }
            }
            
            // Spacer
            Item { width: 10 }
            
            // Year Navigation
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 0 // Force equal 50% split (minus spacing)
                spacing: 5
                
                TextField {
                    text: grid.year
                    font.pixelSize: 16
                    color: theme.textColor
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    selectByMouse: true
                    validator: IntValidator { bottom: 1; top: 9999 }
                    onEditingFinished: grid.year = parseInt(text)
                    background: Rectangle {
                        color: theme.textFieldColor
                        border.color: theme.borderColor
                    }
                }
            }
            IconButton {
                Layout.preferredWidth: 30
                source: "file:assets/icons/arrow-right.svg"
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
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
        
        // Days of Week
        DayOfWeekRow {
            Layout.fillWidth: true
            delegate: Text {
                text: model.shortName
                horizontalAlignment: Text.AlignHCenter
                font.bold: true
                color: theme.textColor
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
                        return theme.secondaryHighlightColor
                    }
                    return "transparent"
                }
                radius: 4
                
                Text {
                    anchors.centerIn: parent
                    text: model.day
                    color: theme.textColor
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
