import QtQuick
import QtQuick.Controls
import QtQuick.Effects

ComboBox {

    id: control

    indicator: Item {
        x: control.width - width - 10
        anchors.verticalCenter: parent.verticalCenter
        width: 20
        height: 20
        Image {
            id: arrowIcon
            source: "file:assets/icons/chevron-down.svg"
            visible: false
        }
        MultiEffect {
            source: arrowIcon
            anchors.fill: parent
            colorization: 1.0
            colorizationColor: theme.textColor
        }
    }

    popup: Popup {
        y: control.height - 1
        width: control.width
        implicitHeight: contentItem.implicitHeight
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: theme.buttonColor
            border.color: theme.borderColor
            radius: 5
            topLeftRadius: 0
            topRightRadius: 0
        }
    }
    
    delegate: ItemDelegate {
        width: parent.width
        text: modelData
        contentItem: Text {
            text: modelData
            color: theme.textColor
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: highlighted ? theme.secondaryHighlightColor : theme.buttonColor
            topLeftRadius: 0
            topRightRadius: 0
            bottomLeftRadius: (index === control.count - 1) ? 4 : 0
            bottomRightRadius: (index === control.count - 1) ? 4 : 0
        }
        highlighted: ListView.isCurrentItem
    }
    
    contentItem: Text {
        leftPadding: 10
        rightPadding: control.indicator.width + control.spacing + 10
        topPadding: 10
        bottomPadding: 10
        text: parent.displayText
        color: theme.textColor
        verticalAlignment: Text.AlignVCenter
    }
    
    background: Rectangle {
        id: backgroundRect
        gradient: Gradient {
            GradientStop { position: 0.0; color: control.down ? theme.buttonPressedStart : Qt.tint(theme.buttonGradientStart, Qt.alpha(theme.bevelLight, 0.7)) }
            GradientStop { position: 2.0 / backgroundRect.height; color: control.down ? theme.buttonPressedStart : theme.buttonGradientStart }
            GradientStop { position: 1.0; color: control.down ? theme.buttonPressedEnd : theme.buttonGradientEnd }
        }
        border.color: theme.borderColor
        radius: 5
        bottomRightRadius: down ? 0 : 5
        bottomLeftRadius: down ? 0 : 5
    }
}