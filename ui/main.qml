import QtQuick
import QtQuick.Controls
import QtQuick.Layouts



ApplicationWindow {
    visible: true
    width: 1000
    height: 700
    title: "Photobase"
    color: theme.backgroundColor


    property int previousTab: 0

    Connections {
        target: galleryModel
        function onFilterChanged(tagName) {
            if (tagName !== "") {
                if (bar.currentIndex !== 0) {
                    previousTab = bar.currentIndex
                }
                bar.currentIndex = 0
            } else {
                if (previousTab !== 0) {
                    bar.currentIndex = previousTab
                    previousTab = 0
                }
            }
        }
    }

    header: TabBar {
        id: bar
        width: parent.width

        contentItem: ListView {
            model: bar.contentModel
            currentIndex: bar.currentIndex
            spacing: bar.spacing
            orientation: ListView.Horizontal
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.AutoFlickIfNeeded
        }

        TabButton {
            text: "Gallery"
        }
        TabButton {
            text: "Tags"
        }
        TabButton {
            text: "Places"
        }
        TabButton {
            text: "Search"
        }
        TabButton {
            text: "Settings"
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: bar.currentIndex

        Gallery {
            id: galleryView
        }
        Tags {
        }
        Places {
        }
        Search {
        }
        Settings {
        }
    }

}
