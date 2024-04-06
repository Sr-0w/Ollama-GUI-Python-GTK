# Ollama GUI Python GTK

## Overview

Ollama GUI Python GTK is a chat application designed for use with the Ollama chat service. It's built using Python and GTK3, providing a basic interface to send and receive messages.

![plot](Images/GUI.png)

## Features

- Select from available Ollama models.
- View and save your chat history.
- Send messages asynchronously.

## Requirements

- Python 3.6+
- GTK3
- GObject Introspection
To ensure users across different Linux distributions can easily install the dependencies for "Ollama GUI Python GTK", here are the commands for the most common distros:

### Ubuntu/Debian

```sh
sudo apt update
sudo apt install python3 python3-gi python3-requests gir1.2-gtk-3.0
```

### Fedora

```sh
sudo dnf install python3 python3-gobject gtk3
```

### CentOS/RHEL

For CentOS/RHEL 7 and 8, you might need to enable EPEL repository to get some of these packages:

```sh
sudo yum install epel-release
sudo yum install python3 python3-gobject gtk3
```

### Arch Linux

```sh
sudo pacman -Syu python python-gobject gtk3
```

### openSUSE

```sh
sudo zypper install python3 python3-gobject gtk3
```

These commands will install Python 3, the GTK3 library, and GObject Introspection, which are essential for running the Ollama GUI Python GTK. Adjustments might be needed based on the specific versions of your Linux distribution or if you're using a non-standard setup.

## Running
### From source

Ensure the Ollama service is accessible. Start the app with:

```sh
python3 ollama_gui_python_gtk.py
```
### Using the binary

```sh
chmod +x ollama_gui_python_gtk
./ollama_gui_python_gtk
```
## And voila !

![plot](Images/Demo.gif)

## Contributing

Feel free to report issues or contribute through pull requests.

## License

Released under GPL-2.0 or later. See [GPL-2.0 License](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html) for more details.
