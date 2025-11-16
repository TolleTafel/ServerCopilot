# ServerCopilot

A sophisticated Minecraft server management application with voice control capabilities, built with PyQt6.

## Overview

ServerCopilot is a one-of-a-kind tool that streamlines your Minecraft server hosting experience and offers greater flexibility in managing your server. It provides an intuitive GUI interface with advanced features like voice control, whitelist management, and system tray integration.

## Features

### Core Features
- **Server Management**: Start, stop, and restart your Minecraft server with ease
- **Real-time Terminal**: Monitor server output in real-time through an integrated terminal
- **Whitelist Management**: Manage player whitelists with support for both default and guest lists
- **System Tray Integration**: Minimize to system tray and control your server from the notification area
- **Custom Server Icons**: Automatically detects and uses your server's icon

### Voice Control
- **Voice Commands**: Control your server using voice commands (wake word: "Copilot")
- **Auto-Start Listener**: Optionally start voice listener on Windows startup
- **Background Operation**: Voice control can run independently in the background
- **Supported Commands**: Start and stop server operations via voice

### User Interface
- **Modern Dark Theme**: Clean, modern interface with dark color scheme
- **Collapsible Layout**: Fold the interface to a minimal view for reduced screen space
- **Multiple Tabs**: Easy navigation between terminal, whitelist, and settings
- **Responsive Design**: Adapts to different screen sizes

### Settings
- **RAM Allocation**: Configure memory allocation for your server
- **Server JAR Selection**: Change server JAR file location
- **Hardware Acceleration**: Optional hardware acceleration (with stability warning)
- **Voice Control Toggle**: Enable/disable voice control from settings
- **Window Position Memory**: Remembers window position between sessions

### Remote Control
- **Firebase Integration**: Remote server control via Firebase (requires credentials)
- **Remote Commands**: Start and stop server remotely through Firebase

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows OS (for voice control and startup features)


### Installation Steps

1. **Download the newest version**

2. **Run the application**

## Usage

### First Launch
1. On first launch, you'll be prompted to select your server's `.jar` file
2. The application will automatically detect your server icon if available
3. Desktop and Start Menu shortcuts will be created automatically

### Starting Your Server
1. Just open the ServerCopilot and your server will start automaticly
2. Monitor server output in the terminal view
3. Use voice commands (if enabled) by saying "Copilot start"

### Managing Whitelist
1. Navigate to the whitelist tab using the sidebar
2. Enter player names or UUIDs in the entry field
3. Use the `+` and `-` buttons to add or remove players
4. Toggle between default and guest whitelist modes

### Voice Control Setup
1. Go to Settings → VoiceControl
2. Enable "Voice Control" toggle
3. Optionally enable "Auto-Start Listener" for automatic startup
4. Say "Copilot" followed by your command ("start" or "stop")

### Remote Control (Optional)
1. Place your `firebase-service-account.json` in the `/APPDATA/Roaming/ServerCopilot/data` folder
2. Remote commands will be automatically enabled
3. Control your server remotely through Firebase

## Known Limitations

- Voice control requires a microphone and may have language limitations
- Hardware acceleration may cause instability on some systems
- Remote control requires Firebase credentials
- Windows-only for voice control auto-start features


## Legal Disclaimer

**IMPORTANT - PLEASE READ CAREFULLY:**

This application (ServerCopilot) is an independent, third-party software tool designed to facilitate the management of Minecraft servers. By using this software, you acknowledge and agree to the following:

1. **No Affiliation**: ServerCopilot is not affiliated with, endorsed by, sponsored by, or officially connected to Microsoft Corporation, Mojang AB, or any of their subsidiaries or affiliates. Minecraft is a trademark of Mojang AB and Microsoft Corporation.

2. **Server Software Requirement**: This application does NOT include Minecraft server software. Users must obtain a valid Minecraft server JAR file through official channels. You are responsible for ensuring compliance with Minecraft's End User License Agreement (EULA) and Terms of Service.

3. **Use at Your Own Risk**: This software is provided "AS IS" without warranty of any kind, either expressed or implied, including but not limited to the implied warranties of merchantability and fitness for a particular purpose. The entire risk as to the quality and performance of the software is with you.

4. **No Liability**: In no event shall the developers or contributors be liable for any damages whatsoever (including, without limitation, damages for loss of business profits, business interruption, loss of business information, or any other pecuniary loss) arising out of the use or inability to use this software.

5. **Voice Control**: The voice control feature processes audio locally on your device. Users are responsible for ensuring compliance with applicable privacy laws and regulations in their jurisdiction.

6. **Remote Control**: Firebase integration and remote control features are optional. Users who enable these features are responsible for securing their Firebase credentials and complying with Firebase's terms of service.

7. **User Responsibility**: You are solely responsible for:
   - Ensuring your use complies with all applicable laws and regulations
   - Managing server content and user access
   - Backing up your server data
   - Monitoring resource usage and server performance

8. **Modifications**: Users who modify or extend this software do so at their own risk and are responsible for any consequences of such modifications.

By downloading, installing, or using ServerCopilot, you acknowledge that you have read this disclaimer, understand it, and agree to be bound by its terms.

---

**Copyright Notice**: ServerCopilot © [Year]. All rights reserved. Minecraft® is a trademark of Mojang AB/Microsoft Corporation.