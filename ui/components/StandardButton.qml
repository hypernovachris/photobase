import QtQuick
import QtQuick.Controls

Button {
    id: control
    property color baseColor: theme.backgroundColor
    property color textColor: theme.textColor

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.textColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        opacity: enabled ? 1.0 : 0.3
    }
}