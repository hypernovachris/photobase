import QtQuick
import QtQuick.Layouts
import ".."

RowLayout {
    id: root
    property int peopleCount: 0
    signal clicked()

    Layout.fillWidth: true
    Layout.alignment: Qt.AlignLeft
    spacing: 10

    // People icon
    IconButton {
        clickable: false
        source: "file:assets/icons/scan-face.svg"
        iconSize: 20
    }

    // Label
    Item {
        // 1. Give the container a size based on its content
        implicitWidth: peopleRow.implicitWidth
        implicitHeight: peopleRow.implicitHeight
        
        // Allow it to be positioned within your external Layout
        Layout.fillWidth: false 

        // 2. The Layout handles the horizontal positioning
        RowLayout {
            id: peopleRow
            anchors.fill: parent
            spacing: 10
            
            Text {
                text: (peopleCount > 0 ? peopleCount : "None") + " detected"
                color: theme.textColor
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 14
            }

            // Link icon
            IconButton {
                clickable: false
                source: "file:assets/icons/external-link-3px.svg"
                iconSize: 16
            }
        }

        // 3. The MouseArea fills the entire Item (Text + Icon)
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.clicked()
        }
    }
}
