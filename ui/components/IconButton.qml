import QtQuick
import QtQuick.Effects

Item {
    id: root
    
    // Public Properties
    property string source
    property int iconSize: 20
    property int iconWidth: iconSize
    property int iconHeight: iconSize
    property color color: theme.textColor
    property color hoverColor: theme.textColor // Optional hover color
    property alias cursorShape: mouseArea.cursorShape
    property bool clickable: true
    
    // Signals
    signal clicked(var mouse)
    signal entered()
    signal exited()
    
    // Size is determined by iconWidth and iconHeight by default, but can be overridden
    implicitWidth: iconWidth
    implicitHeight: iconHeight
    
    Image {
        id: icon
        source: root.source
        sourceSize.width: root.iconWidth
        sourceSize.height: root.iconHeight
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
