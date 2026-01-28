import QtQuick
import QtQuick.Controls

CheckBox {
    id: control

    property color boxColor: theme.textFieldColor
    property color checkColor: theme.textColor
    property color borderColor: theme.borderColor

    spacing: 10
    
    hoverEnabled: true

    indicator: Rectangle {
        implicitWidth: 24
        implicitHeight: 24
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        radius: 3
        
        border.color: control.borderColor
        border.width: 1

 
        gradient: Gradient {
            GradientStop { position: 0.0; color: control.checked ? theme.buttonGradientStart : theme.buttonPressedStart }
            GradientStop { position: 1.0; color: control.checked ? theme.buttonGradientEnd : theme.buttonPressedEnd }
        }
        


        Text {
            anchors.centerIn: parent
            text: "✔" 
            font.pixelSize: 12
            color: control.checkColor
            visible: control.checked
            // renderType: Text.NativeRendering
        }
    }

    contentItem: Text {
        text: control.text
        font: control.font
        opacity: enabled ? 1.0 : 0.5
        color: theme.textColor
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + control.spacing
    }
}
