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
    background: Rectangle {
        topLeftRadius: 2
        topRightRadius: 2
        color: theme.borderColor
        opacity: control.checked ? 1.0 : 0.5
        implicitHeight: 16

        // inner rectangle to create effect of border on top, left, and right:
        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 1
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            anchors.bottomMargin: control.checked ? 0 : 1
            topLeftRadius: 2
            topRightRadius: 2
            color: control.checked ? theme.backgroundColor : theme.headerColor
        }
    }
}
