import QtQuick
import QtQuick.Controls

TabButton {
    id: control
    // Custom content item to handle bold text
    font.pixelSize: 15
    contentItem: Text {
        text: control.text
        font: Qt.font({
            family: control.font.family,
            pixelSize: control.font.pixelSize,
        })
        opacity: control.checked ? 1.0 : 0.8
        color: theme.textColor 
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignBottom
        elide: Text.ElideRight
    }
    width: implicitWidth
    leftPadding: 20
    rightPadding: 20

    // Custom background
    background: Rectangle { // Main container / Border
        topLeftRadius: 4
        topRightRadius: 4
        color: theme.borderColor
        
        // Ensure inactive tabs look "behind" or lower
        height: control.checked ? parent.height : parent.height - 2
        anchors.bottom: parent.bottom

        // Inner Gradient Background
        Rectangle {
            id: innerGradient
            anchors.fill: parent
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            anchors.topMargin: 1
            // If checked, connect to content (no bottom border). If unchecked, show bottom border.
            anchors.bottomMargin: 1 
            
            topLeftRadius: 3
            topRightRadius: 3
            
            gradient: Gradient {
                GradientStop { position: 0.0; color: control.checked ? Qt.tint(theme.buttonGradientStart, Qt.alpha(theme.bevelLight, 0.7)) : theme.headerGradientEnd }
                GradientStop { position: 2.0 / innerGradient.height; color: control.checked ? theme.buttonGradientStart : theme.headerGradientEnd }
                GradientStop { position: 1.0; color: control.checked ? theme.backgroundColor : theme.headerGradientEnd }
            }
        }
    }
}
