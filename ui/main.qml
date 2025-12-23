import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 1000
    height: 700
    title: "Photobase"

    Connections {
        target: galleryModel
        function onFilterChanged(tagName) {
            if (tagName !== "") {
                bar.currentIndex = 0
            }
        }
    }

    header: TabBar {
        id: bar
        width: parent.width
        TabButton {
            text: "Gallery"
        }
        TabButton {
            text: "Tags"
        }
        TabButton {
            text: "People"
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
        }
        Tags {
        }
        People {
        }
        Places {
        }
        Search {
        }
        Settings {
        }
    }
}
