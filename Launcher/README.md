# 🧩 NeoMLoader [Rodina] [![Download Latest Release](https://img.shields.io/github/v/release/txryfx/ArizonaTools?label=Download%20Latest%20APK&style=for-the-badge&color=success)](https://github.com/txryfx/ArizonaTools/releases/latest)

<img width="900" height="400" alt="Logo" src="https://github.com/user-attachments/assets/e9e33c68-1e3f-4d88-9338-00ef7613d416" />

An **external automation tool** (patcher) that adds **Lua scripting support** to the **[Rodina](https://arzgame.online/)** client through the external **[NeoMLoader](https://t.me/neomloader)** library.

This repository contains a build pipeline that dynamically patches the game. It is responsible for:
- 📥 Downloading the official client and decompiling it locally
- 🧩 Automatically unpacking NeoMLoader resource files
- 🗒️ Automatically installing default Lua scripts & libs
- 🔄 Checking if the launcher version is up to date
- 💰 Managing Unity Ads behavior *(to support the continued development of this tool)*


> ⚠️ **LEGAL DISCLAIMER** 
> This repository **does not contain** any original game files, assets, or proprietary code. It is strictly a build automation tool (a patcher) that modifies the official client locally via CI/CD pipelines. The files provided in the Releases tab are automated build artifacts provided solely for research, interoperability, and informational purposes only.  
> This project is **independent and not affiliated with, endorsed by, or connected to Arizona Games, Rockstar Games, NeoMLoader Team or their partners.** 
> All trademarks and copyrights belong to their respective owners.

---

## 📥 Installation (For Players)

If you only want to play, you don't need to build the project yourself. 

Our automated CI/CD pipeline builds the latest version every time the game updates.

1. Go to the [Releases page](https://github.com/txryfx/ArizonaTools/releases/latest).
2. Download the latest `arizona` or `rodina` apk.
3. Install the APK on your Android device and grant the necessary permissions.
4. Use the `/amenu` command in-game to manage your scripts!

---

# ⚙️ Features

### 🧩 Core Functionality
- 1️⃣ Adds **Lua scripting** support via **NeoMLoader**
- 2️⃣ Integrates **Rodina Tools** module and **Unity Ads** SDK

### ⚙️ NeoMLoader Integration
- Provides Lua-based scripting support & includes required resource files
- Installs default Lua scripts and required libraries automatically

### 🧰 Rodina Tools (Arizona Tools)
- Automatically extracts required Lua libraries and helper assets
- Manages bundled Arizona Tools modules and performs version checks

### 💰 Unity Ads
- Loads and displays ads using the Unity SDK  
- Ads appear **once at startup** and **do not interrupt gameplay** 

---

## 📂 Project Structure (For Developers)

This project uses a fully automated, dynamic build pipeline.

```bash
├── .env                        # Environment variables for keystore (optional)
├── gitbuild.jks                     # Keystore for signing the final APK (optional)
├── requirements.txt            # Python dependencies for the build environment
├── main.py                     # The Orchestrator (Defines build targets and runs subprocesses)
├── build_launcher.py           # The Build Engine (Worker script for individual isolated builds)
├── background_home.webp        # The background image
├── files/                      # Payload directory (copied directly into the decompiled APK)
│   ├── assets/                 # Custom resources, Lua scripts & configs
│   └── lib/                    # Base NeoMLoader native libraries (.so)
├── java/                       # Java source code for the wrapper
│   ├── Ads.java                # Unity Ads integration
│   ├── AssetExtractor.java     # Extracts required resource files
│   ├── CheckUpdate.java        # Update check manager
│   └── RodinaTools.java        # Core logic & checks
└── libs/                       # Build tools & heavy vendor archives
    ├── android.jar             # Android SDK for compiling Java code                  
    ├── apksigner.jar           # Signs the final rebuilt APK
    ├── apktool.jar             # Decompiles and recompiles the APK
    ├── baksmali.jar            # Disassembles .dex files into .smali format
    ├── d8.jar                  # Converts Java .class files to Android .dex
    ├── unity-ads-4.4.1.jar     # Unity Ads SDK (used for project monetization)
    ├── unity-scaradapter...jar # Unity Ads SDK (used for project monetization)
    └── neomloader.zip          # Vendor NeoMLoader core (unpacked dynamically)
```

# 🚀 Build Process (Local Development)

If you want to compile the project yourself:

### 1️⃣ Requirements
- **Python 3.10+** (requires requests and python-dotenv modules)
- **Java 8+** (for dynamic compilation and apktool)
- **Keystore for signing the final APK** *(if not provided — unsigned apk will be saved)*
---
### 2️⃣ Build Steps

1. **Clone** this repository to your local machine:
```bash
git clone https://github.com/txryfx/ArizonaTools.git
cd ArizonaTools/launcher
```
2. Install **Python** dependencies:
```bash
pip install -r requirements.txt
```
3. Set **your keystore** credentials in the **.env** file located in the project root

```bash
KEY_ALIAS="alias"
KEY_PASS="key_password"
KEYSTORE_PASS="keystore_password" # optional if same as KEY_PASS
```

4. Run the orchestrator script in the terminal:
```bash
python main.py
```
The script will sequentially launch isolated subprocesses for each target defined in main.py (e.g., Arizona, then Rodina). 

For each target, it will automatically download the original APK, decompile it, inject the Smali code, auto-adapt Java paths, build the project, and sign the final APK.

Tip: If you want to build only a specific target, you can run the builder directly:
```bash
python build_launcher.py arizona
# or
python build_launcher.py rodina
```

---

# 📜 License & Copyright

- **The code in this repository** (build scripts, Java wrappers, and custom Lua helpers) is released under the [MIT License](LICENSE). You are free to modify and distribute these specific tools.
- **NeoMLoader** is an another project created by [bymaga0](https://t.me/neomloader). Please refer to bymaga0 for specific licensing terms.
- **Rodina Mobile** and all related trademarks, copyrights, and assets are the property of their respective owners. This project claims no ownership over the original game client.
