import QtQuick
import QtQuick.Controls
import QtQuick.Effects

Item {
    id: root
    
    // Public Properties
    property string source
    property int iconSize: 20
    property color color: theme.textColor
    property color hoverColor: theme.textColor // Optional hover color
    property alias cursorShape: mouseArea.cursorShape
    property bool clickable: true
    
    // Signals
    signal clicked(var mouse)
    signal entered()
    signal exited()
    
    // Size is determined by iconSize by default, but can be overridden
    implicitWidth: iconSize
    implicitHeight: iconSize
    
    Image {
        id: icon
        source: root.source
        sourceSize.width: root.iconSize
        sourceSize.height: root.iconSize
        visible: false
        anchors.centerIn: parent
    }

    MultiEffect {
        source: icon
        anchors.fill: icon
        colorization: 1.0
        colorizationColor: (root.clickable && mouseArea.containsMouse) ? root.hoverColor : root.color
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: root.clickable
        hoverEnabled: true
        cursorShape: root.clickable ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: (mouse) => root.clicked(mouse)
        onEntered: root.entered()
        onExited: root.exited()
    }
}
