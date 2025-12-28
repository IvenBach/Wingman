# Wingman

A suite of enhancements for the UI of the text-based game, Olmran

## Prerequisites (Critical)

Because this tool sniffs network packets to read game data, you need two things installed:

1.  **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
2.  **Npcap (Windows)** or **libpcap (Linux)**:
    * **Windows Users:** You MUST install [Npcap](https://npcap.com/#download).
    * *During installation, check the box: "Install Npcap in WinPcap API-compatible Mode".*
    
## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/BSFSH/Wingman
    cd Wingman
    ```

2.  **Run the app:**
    ```bash
    python run.py
    ```

## Configuration

By default, the tracker listens for traffic from the game server `18.119.153.121` on port `4000`.

If you need to track a different server:
1.  Open `src/Wingman/core/network_listener.py`.
2.  Edit the `self.target_ip` and `self.target_port` variables.

## How to Run

**Note:** You must run this application with **Administrator/Root** privileges so it can access your network card.

**Windows (PowerShell/CMD):**
1.  Right-click your terminal and select **"Run as Administrator"**.
2.  Navigate to the project folder.
3.  Run the application:
    ```bash
    python src/Wingman/main.py
    ```

**Linux/Mac:**
```bash
sudo python3 src/Wingman/main.py
```
**Note:** Linux/Mac compatibility is completely untested.
