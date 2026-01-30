import QtQuick
import QtQuick.Layouts
import ".."

Flow {
    property var tags: []
    // property bool visible: true // Removed to avoid overriding final property

    
    signal removeTagRequested(string tagName)
    signal addTagRequested()

    Layout.fillWidth: true
    spacing: 10
    readonly property int rowHeight: 30

    // Tags icon
    Item {
        height: parent.rowHeight
        width: 20
        IconButton {
            anchors.centerIn: parent
            clickable: false
            source: "file:assets/icons/tag.svg"
            iconSize: 20
        }
    }

    // Tags List
    Repeater {
        visible: tags.length > 0
        model: tags
        delegate: Rectangle {
            height: 30
            width: tagRow.implicitWidth + 10
            border.color: theme.borderColor
            
            Row {
                id: tagRow
                anchors.centerIn: parent
                spacing: 5
                padding: 5
                
                Text {
                    text: modelData
                    color: theme.textColor
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                IconButton {
                    width: 16
                    height: 16
                    iconSize: 16
                    anchors.verticalCenter: parent.verticalCenter
                    source: "file:assets/icons/x.svg"
                    color: theme.textColor
                    onClicked: removeTagRequested(modelData)
                }
            }
        }
    }

    // Add Tag Button
    Item {
        height: parent.rowHeight
        width: 20
        Item {
            width: 20
            height: 20
            visible: true
            anchors.verticalCenter: parent.verticalCenter
            
            IconButton {
                anchors.fill: parent
                source: "file:assets/icons/plus.svg"
                color: theme.textColor
                onClicked: addTagRequested()
            }
        }
    }
}
