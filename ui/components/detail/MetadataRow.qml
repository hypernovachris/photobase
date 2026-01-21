import QtQuick
import QtQuick.Layouts
import ".."

RowLayout {
    property string iconSource: ""
    property string text: ""
    property bool isLink: false
    property bool isUnavailable: text === "Unavailable" || text === ""
    property int iconWidth: 20
    property int iconHeight: 20
    
    signal linkActivated()

    Layout.fillWidth: true
    Layout.alignment: Qt.AlignLeft
    spacing: 10

    IconButton {
        clickable: false
        source: iconSource
        iconWidth: parent.iconWidth
        iconHeight: parent.iconHeight
    }

    Text {
        text: parent.text || "Unavailable"
        font.italic: parent.isUnavailable
        font.pixelSize: 14
        color: theme.textColor
        elide: Text.ElideRight
        Layout.fillWidth: true
        opacity: parent.isUnavailable ? 0.7 : 1.0

        MouseArea {
            anchors.fill: parent
            enabled: parent.parent.isLink
            cursorShape: parent.parent.isLink ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: parent.parent.linkActivated()
        }
    }
}
