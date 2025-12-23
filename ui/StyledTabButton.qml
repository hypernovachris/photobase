import QtQuick
import QtQuick.Controls

TabButton {
    id: control
    
    // Custom content item to handle bold text
    contentItem: Text {
        text: control.text
        font: Qt.font({
            family: control.font.family,
            pixelSize: control.font.pixelSize,
            bold: control.checked
        })
        opacity: enabled ? 1.0 : 0.3
        color: theme.textColor 
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    // Custom background
    background: Rectangle {
        implicitHeight: 40
        color: "transparent" // No background color change
        
        // Underline indicator
        Rectangle {
            width: parent.width
            height: 3
            anchors.bottom: parent.bottom
            color: theme.highlightColor // Use theme highlight color
            visible: control.checked
        }
    }
}
