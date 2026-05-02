# REALITY V3

### **Project Overview**
**Reality V3** is a high-performance **MaaS (Malware-as-a-Service)** Proof of Concept designed to demonstrate modular data orchestration and exfiltration architecture. 

This repository exists to showcase software engineering concepts within a red-team context. **I will not provide setup instructions, deployment support, or troubleshooting.** If you cannot navigate the codebase yourself, this project is not for you.

---

### **Core Capabilities**

*   **Dual-Hooking Redundancy:** Built-in logic to route exfiltrated data through multiple concurrent webhooks for redundancy and logging persistence.
*   **Modular Architecture:** The system is decoupled into specific modules (see `/modules`) allowing for targeted execution without bloat.
*   **Firebase Integration:** Utilizes `firebase_config.py` for dynamic backend management and remote configuration.
*   **Asynchronous Processing:** Designed to handle multiple data streams simultaneously to ensure speed and efficiency.

---

### **Module Breakdown**

The logic is categorized into specialized handlers to ensure high success rates and low resource footprint:

| Module | Technical Focus |
| :--- | :--- |
| `browser_stealer.py` | Chromium-based credential extraction and cookie parsing. |
| `discord_stealer.py` | Token identification and account metadata retrieval. |
| `network_stealer.py` | Network interface mapping and IP/DNS profiling. |
| `wallet_stealer.py` | Cold wallet and browser-extension crypto asset detection. |
| `messaging_stealer.py` | Session data extraction for desktop messaging applications. |
| `ssh_git_ftp.py` | Developer-centric credential auditing (SSH keys, `.gitconfig`, FTP hosts). |
| `screenshot.py` | Asynchronous screen capture and temporary buffer storage. |

---

### **Execution Flow**

1.  **Initialization:** `main.py` triggers the environment audit.
2.  **Configuration:** `config.py` loads the runtime parameters.
3.  **Browser Cookie Stealing** Logic contained in `injector.py` and `chromelevator_x64.exe` handles process-level interactions.
4.  **Exfiltration:** Data is compressed and dispatched via the dual-hook system defined in the build config.

---

### **Final Note**
This is a demonstration of how modern MaaS platforms are structured. It is intended for security researchers and developers interested in offensive security architecture. 

**Stars are appreciated if you find the modular design or dual-hooking logic insightful.**
