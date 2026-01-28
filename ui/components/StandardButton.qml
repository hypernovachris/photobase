import QtQuick
import QtQuick.Controls

Button {
    id: control

    property color baseColor: theme.buttonColor
    property color textColor: theme.textColor

    contentItem: Text {
        text: control.text
        font: control.font
        opacity: enabled ? 1.0 : 0.3
        color: control.textColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 80
        implicitHeight: 24
        radius: 4
        id: backgroundRect
        
        border.color: theme.borderColor
        border.width: 1

        gradient: Gradient {
            GradientStop { position: 0.0; color: control.down ? theme.buttonPressedStart : Qt.tint(theme.buttonGradientStart, Qt.alpha(theme.bevelLight, 0.7)) }
            GradientStop { position: 2.0 / backgroundRect.height; color: control.down ? theme.buttonPressedStart : theme.buttonGradientStart }
            GradientStop { position: 1.0; color: control.down ? theme.buttonPressedEnd : theme.buttonGradientEnd }
        }
    }
}
