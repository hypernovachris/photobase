import QtQuick
import QtQuick.Layouts
import ".."

RowLayout {
    property string currentImagePath: ""
    signal closeRequested()
    signal openFileRequested()

    Layout.fillWidth: true
    spacing: 10

    // 1. NESTED LAYOUT (Holds Name + Ext + Spacer)
    RowLayout {
        spacing: 0
        Layout.fillWidth: true 

        // A. FILENAME
        Text {
            id: filenameText
            text: {
                if (!currentImagePath) return ""
                var name = currentImagePath.split('\\').pop().split('/').pop()
                var lastDot = name.lastIndexOf('.')
                return lastDot > 0 ? name.substring(0, lastDot) : name
            }
            font.pixelSize: 24
            font.bold: true
            color: theme.textColor
            
            elide: Text.ElideRight
            Layout.alignment: Qt.AlignBaseline
            
            Layout.fillWidth: true             // Enable dynamic sizing
            Layout.minimumWidth: 0             // Allow shrinking (eliding)
            Layout.maximumWidth: implicitWidth // Prevent growing (keeps extension attached)

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: openFileRequested()
            }
        }

        // B. EXTENSION
        Text {
            text: currentImagePath ? "." + currentImagePath.split('\\').pop().split('/').pop().split('.').pop().toUpperCase() : ""
            font.pixelSize: 16
            font.bold: true
            color: theme.textColor
            Layout.alignment: Qt.AlignBaseline
            
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: openFileRequested()
            }
        }

        // C. INTERNAL SPACER
        Item {
            Layout.fillWidth: true 
        }
    }

    // 2. CLOSE BUTTON
    Item {
        width: 30
        height: 30
        Layout.alignment: Qt.AlignVCenter

        IconButton {
            anchors.fill: parent
            source: "file:assets/icons/x.svg"
            iconSize: 30
            onClicked: closeRequested()
        }
    }
}
