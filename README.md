
# Photobase

  

Photobase is a modern photo management application built with Python and PyQt6 (QML). It allows you to organize, view, and tag your photo collection with a sleek, responsive user interface.

  

## Features

  

-  **Fast Photo Gallery**: You've probably noticed that browsing large directories in the File Explorer is slow, especially on HDDs. Photobase solves this by loading image details into a database. Browse your entire photo library with a smooth, grid-based interface. Double-click an image to open it, right-click an image to open the context menu. Bulk actions are supported: use Ctrl or Shift to select multiple images, then right click.

-  **Image Viewer**: View, zoom, and panacross high-resolution images in the application. On the right, view file info. Click the filename to open it in the default image viewer, click the path to reveal it in the file explorer.

- **EXIF Metadata Support**: If present, Photobase uses the "date taken" field in an image's EXIF data, ensuring that dates remain stable when images are copied or modified. Capture information (camera, lens) can viewed and used to filter images in the Search tab.

-  **Tag Management**: Organize your photos by adding and editing tags. Tags can be renamed by clicking their name in the Tags tab.

-  **Search & Filter**: Quickly find photos by date, tags, or other metadata. Filters can also be conjunctively combined.

-  **HEIC Support**: Native support for HEIC/HEIF image formats.

-  **Customizable Settings**: Configure scan paths and application preferences.

-  **Theming**: Automatically respects your system's dark mode preference.

  

## Prerequisites

  

- Python 3.x

- pip

  

## Installation

  

1. Clone the repository:

```bash

git clone <repository-url>

cd photobase

```

  

2. Install the required dependencies:

```bash

pip install -r requirements.txt

```

  

## Usage

  

To start the application, run the `main.py` script:

  

```bash

python  main.py

```

  

On the first run, you will be asked to add a directory to Photobase.


## License

  

See the `LICENSE` file for details.
