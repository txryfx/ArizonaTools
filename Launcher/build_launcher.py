import subprocess, os, re, shutil, glob, requests, zipfile, json, sys
from dotenv import load_dotenv
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

if len(sys.argv) != 2 or sys.argv[1] not in {"arizona", "rodina"}:
    raise RuntimeError("[INFO] 👉 Usage: python builder.py <arizona|rodina>")

PROJECTS_APK = {
    "arizona": "https://mob2.maz-ins.com/client/release/bin/app-arizona-release_web.apk",
    "rodina": "https://mob2.azinternal.com/client/release/bin/app-rodina-release_web.apk",
}

DOWNLOAD_URL = PROJECTS_APK[sys.argv[1]]
APK_DISPLAY_NAME = "RodinaTools"

##################################################################################################################

PATH = os.path.dirname(__file__).replace('\\', '/')
load_dotenv(os.path.join(PATH, ".env"))

APKTOOL_PATH = PATH + "/libs/apktool.jar"

APK_NAME = DOWNLOAD_URL.split("/")[-1].removesuffix(".apk")

DECODED_DIR = PATH + "/" + APK_NAME

APK_PATH = DECODED_DIR + ".apk"

##################################################################################################################

def download_with_progress(url, dest):
    print(f"[INFO] 📥 Downloading latest original APK from {url}...")
    r = requests.get(url, stream=True, allow_redirects=True)
    r.raise_for_status()

    content_type = r.headers.get("Content-Type", "").lower()
    if "application/vnd.android.package-archive" not in content_type and "application/octet-stream" not in content_type and "application/zip" not in content_type:
        if "text/html" in content_type or "text/plain" in content_type:
            raise RuntimeError(f"❗ Server returned {content_type} instead of APK. URL may be broken or require auth.")

    total = int(r.headers.get("Content-Length", 0))
    downloaded = 0
    start = time.time()
    last_print = 0

    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 64):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)

            now = time.time()
            if now - last_print >= 0.3:
                last_print = now
                elapsed = now - start
                speed = downloaded / elapsed if elapsed > 0 else 0

                if total > 0:
                    percent = downloaded / total * 100
                    bar_len = 30
                    filled = int(bar_len * downloaded / total)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    print(f"\r[INFO] 📥 [{bar}] {percent:5.1f}%  "
                          f"{downloaded/1024/1024:6.1f}/{total/1024/1024:.1f} MB  "
                          f"{speed/1024/1024:5.2f} MB/s", end="", flush=True)
                else:
                    print(f"\r[INFO] 📥 {downloaded/1024/1024:6.1f} MB  "
                          f"{speed/1024/1024:5.2f} MB/s", end="", flush=True)

    print()
    # Проверка магических байтов: APK/ZIP начинается с "PK"
    with open(dest, "rb") as f:
        magic = f.read(2)
    if magic != b"PK":
        os.remove(dest)
        raise RuntimeError(f"❗ Downloaded file is not a valid APK (magic bytes: {magic!r}). Check the URL: {url}")

    print("[INFO] ✅ APK downloaded successfully!")

if not os.path.exists(APK_PATH):
    download_with_progress(DOWNLOAD_URL, APK_PATH)

##################################################################################################################

if os.path.exists(DECODED_DIR):
    print("[INFO] 🗑️ Delete old decompiled app folder...")
    shutil.rmtree(DECODED_DIR, ignore_errors=True)

print("[INFO] ⚙️ Decompiling APK...")
subprocess.run(["java", "-jar", APKTOOL_PATH, "d", APK_PATH, "-o", DECODED_DIR, "--force"], check=True)
print("[INFO] ✅ APK decompiled successfully!")

#################################################################################################################

APKTOOL_YML_PATH = DECODED_DIR + "/apktool.yml"

print("[INFO] 📦 Getting app version...")

with open(APKTOOL_YML_PATH, "r", encoding="utf-8") as file:
    apktool_yml = file.read()

match = re.search(r"^\s*versionName:\s*['\"]?([^'\"\r\n]+)", apktool_yml, re.MULTILINE)

if match:
    version_app = match.group(1).strip()
else:
    version_app = "lua"

print(f"[INFO] ℹ️ App version: {version_app}")

##################################################################################################################

LIB_PATH = DECODED_DIR + "/lib/armeabi-v7a"

print(f"[INFO] 🗑️ Delete armeabi-v7a lib folder (Neomloader only 64bit)...")

if os.path.exists(LIB_PATH):
    shutil.rmtree(LIB_PATH)
    print("[INFO] ✅ Folder armeabi-v7a removed successfully!")

##################################################################################################################

SRC_FILES = PATH + "/files"

print("[INFO] 🔧 Adding \"files\" to original client...")

for root, dirs, files in os.walk(SRC_FILES):
    for file in files:
        src_file = os.path.join(root, file)
        dest_file = os.path.join(DECODED_DIR, os.path.relpath(src_file, SRC_FILES))
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        shutil.copy2(src_file, dest_file)

print("[INFO] ✅ Folder \"files\" added successfully!")

##################################################################################################################

NEOMLOADER_ZIP_PATH = "libs/neomloader.zip"
NEOMLOADER_TARGET_DIR = os.path.join(DECODED_DIR, "assets", "neomloader")

print("[INFO] 🔧 Extracting NeoMLoader core (libs & default scripts)...")
    
if not os.path.exists(NEOMLOADER_ZIP_PATH):
    raise RuntimeError("❗ NeoMLoader zip not found!")

try:
    with zipfile.ZipFile(NEOMLOADER_ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(NEOMLOADER_TARGET_DIR)
    print("[INFO] ✅ NeoMLoader core extracted successfully!")
except Exception as e:
    raise RuntimeError(f"❗ Failed to extract NeoMLoader core: {e}")

##################################################################################################################

SMALI_CLASSES = glob.glob(DECODED_DIR + "/smali_classes*")

SMALI_PATH = ""

for smali_dir in SMALI_CLASSES:
    smali_dir = smali_dir.replace('\\', '/')
    potential_path = smali_dir + "/com/arizona/game/GTASA.smali"
    if os.path.isfile(potential_path):
        SMALI_PATH = smali_dir.replace(DECODED_DIR, '')
        break

if SMALI_PATH == "":
    raise RuntimeError("❗ Failed to find GTASA smali folder!")

# ##################################################################################################################

GTASA_INTERNAL_PATH = DECODED_DIR + SMALI_PATH + "/com/arizona/game/GTASA.smali"

print("[INFO] 🔗 Injecting NeoMLoader into GTASA.smali...")

with open(GTASA_INTERNAL_PATH, "r", encoding="utf-8") as file:
    smali_lines = file.readlines()

check_find_ag_client = False
check_connect = False

for i, line in enumerate(smali_lines):
    match1 = re.search(r'const-string(?:/jumbo)? (v\d+), "ag-client"', line)
    if match1:
        check_find_ag_client = True
        var_name = match1.group(1)
        
        if f"invoke-static {{{var_name}}}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V" in smali_lines[i + 2]:
            smali_lines.insert(i + 4, f'\n    const-string {var_name}, "neomloader"\n\n    invoke-static {{{var_name}}}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n\n')
            print("[INFO] ✅ NeoMLoader injected successfully!")
            check_connect = True
            break

if not check_find_ag_client:
    raise RuntimeError("❌ Failed to locate 'ag-client' in GTASA.smali.")

if not check_connect:
    raise RuntimeError("❌ Failed to locate 'ag-client' loadLibrary call in GTASA.smali.")

with open(GTASA_INTERNAL_PATH, "w", encoding="utf-8") as file:
    file.writelines(smali_lines)

##################################################################################################################

smali_numbers = []

for path in SMALI_CLASSES:
    name = os.path.basename(path)
    if name.startswith("smali_classes"):
        num = name.replace("smali_classes", "")
        if num.isdigit():
            smali_numbers.append(int(num))

if not smali_numbers:
    raise RuntimeError("❌ No smali_classes folders found!")

LATEST_SMALI = max(smali_numbers)

##################################################################################################################

PATH_SMALI_TOOLS = DECODED_DIR + f"/smali_classes{LATEST_SMALI + 1}"

print("[INFO] 🔧 Compiling Rodina Tools from java files to smali...")

def compile_java_to_smali():
    classpath = f"libs/android.jar{os.pathsep}libs/unity-ads-4.4.1.jar"
    java_files = sorted(glob.glob(os.path.join("java", "*.java")))
    if not java_files:
        raise RuntimeError("Java source files not found in java/")

    game_id = os.getenv("UNITY_ADS_GAME_ID", "800432055").strip()
    placement_id = os.getenv("UNITY_ADS_PLACEMENT_ID", "BP_Interstitial_Android").strip()
    test_mode = os.getenv("UNITY_ADS_TEST_MODE", "false").strip().lower()
    if not re.fullmatch(r"[0-9]+", game_id) or not placement_id:
        raise RuntimeError("Set a numeric Android UNITY_ADS_GAME_ID and a non-empty UNITY_ADS_PLACEMENT_ID")
    if test_mode not in {"true", "false"}:
        raise RuntimeError("UNITY_ADS_TEST_MODE must be true or false")

    with TemporaryDirectory(prefix="launcher-java-") as temp:
        build_dir = Path(temp)
        config_source = build_dir / "AdsConfig.java"
        config_source.write_text(
            "package com.arizona.launcher;\n"
            "final class AdsConfig {\n"
            f"    static final String GAME_ID = {json.dumps(game_id)};\n"
            f"    static final String PLACEMENT_ID = {json.dumps(placement_id)};\n"
            f"    static final boolean TEST_MODE = {test_mode};\n"
            "}\n",
            encoding="utf-8",
        )
        classes_dir = build_dir / "classes"
        classes_dir.mkdir()
        subprocess.run([
            "javac", "--release", "8", "-encoding", "UTF-8",
            "-cp", classpath, "-d", str(classes_dir), *java_files, str(config_source),
        ], check=True)
        subprocess.run([
            "java", "-cp", "libs/d8.jar", "com.android.tools.r8.D8",
            "--release", "--output", temp,
            "--lib", "libs/android.jar", "--lib", "libs/unity-ads-4.4.1.jar",
            *sorted(str(path) for path in classes_dir.rglob("*.class")),
        ], check=True)
        subprocess.run([
            "java", "-jar", "libs/baksmali.jar", "d",
            str(build_dir / "classes.dex"), "-o", PATH_SMALI_TOOLS,
        ], check=True)

compile_java_to_smali()

##################################################################################################################

PATH_SMALI_ADS = DECODED_DIR + f"/smali_classes{LATEST_SMALI + 2}"

print("[INFO] 🔧 Compiling Unity Ads from jar to smali...")

def compile_unity_ads_to_smali():
    unity_jars = [
        "libs/unity-ads-4.4.1.jar",
        "libs/unity-scaradapter-common.jar",
        "libs/unity-scaradapter-1920.jar",
        "libs/unity-scaradapter-1950.jar",
        "libs/unity-scaradapter-2000.jar",
    ]
    temp_dex_dir = "temp_unity_dex"

    for jar in unity_jars:
        if not os.path.exists(jar):
            raise RuntimeError(f"❗ Jar not found: {jar}")

    os.makedirs(temp_dex_dir, exist_ok=True)

    try:
        print("[INFO] ⚙️ Unity Ads Jar -> Dex...")
        
        subprocess.run([
            "java",
            "-cp", "libs/d8.jar",
            "com.android.tools.r8.D8",
            "--release",
            "--output", temp_dex_dir,
            "--lib", "libs/android.jar",
            *unity_jars
        ], check=True)

        print("[INFO] ⚙️ Dex -> Smali...")

        dex_file = os.path.join(temp_dex_dir, "classes.dex")
        subprocess.run([
            "java", "-jar", "libs/baksmali.jar",
            "d", dex_file,
            "-o", PATH_SMALI_ADS
        ], check=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"❗ Failed compile Unity Ads: {e}")
    finally:
        if os.path.exists(temp_dex_dir):
            shutil.rmtree(temp_dex_dir)

    print("[INFO] ✅ Unity Ads compiled successfully!")

compile_unity_ads_to_smali()

##################################################################################################################

print("[INFO] 🔧 Moving androidx folder to smali_classes...")

src_move = os.path.join(DECODED_DIR, "smali_classes3", "androidx")
dst_move = os.path.join(DECODED_DIR, f"smali_classes{LATEST_SMALI + 3}", "androidx")
if os.path.exists(src_move):
    os.makedirs(os.path.dirname(dst_move), exist_ok=True)
    shutil.move(src_move, dst_move)

##################################################################################################################

MANIFEST_PATH = DECODED_DIR + "/AndroidManifest.xml"

print("[INFO] 📢 Adding Unity Ads activities to AndroidManifest.xml...")

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID_NS)
android = "{" + ANDROID_NS + "}"
manifest = ET.parse(MANIFEST_PATH)
root = manifest.getroot()
application = root.find("application")
if application is None:
    raise RuntimeError("AndroidManifest.xml has no application element")

permissions = {entry.get(android + "name") for entry in root.findall("uses-permission")}
for name in ("android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE",
             "com.google.android.gms.permission.AD_ID"):
    if name not in permissions:
        root.insert(list(root).index(application), ET.Element("uses-permission", {android + "name": name}))

activities = {entry.get(android + "name"): entry for entry in application.findall("activity")}
for suffix, transparent, accelerated in (
    ("AdUnitActivity", False, True),
    ("AdUnitTransparentActivity", True, True),
    ("AdUnitTransparentSoftwareActivity", True, False),
    ("AdUnitSoftwareActivity", False, False),
):
    name = "com.unity3d.services.ads.adunit." + suffix
    activity = activities.get(name)
    if activity is None:
        activity = ET.SubElement(application, "activity", {android + "name": name})
    activity.set(android + "exported", "false")
    activity.set(android + "hardwareAccelerated", "true" if accelerated else "false")
    activity.set(android + "configChanges",
                 "fontScale|keyboard|keyboardHidden|locale|mnc|mcc|navigation|"
                 "orientation|screenLayout|screenSize|smallestScreenSize|uiMode|touchscreen")
    theme = "Theme.Translucent" if transparent else "Theme"
    activity.set(android + "theme", f"@android:style/{theme}.NoTitleBar.Fullscreen")

ET.indent(manifest, space="    ")
manifest.write(MANIFEST_PATH, encoding="utf-8", xml_declaration=True)

##################################################################################################################

ARZ_SMALI_PATH = ""

for smali_dir in SMALI_CLASSES:
    smali_dir = smali_dir.replace('\\', '/')
    potential_path = smali_dir + "/com/arizona/launcher/UpdateService.smali"
    if os.path.isfile(potential_path):
        ARZ_SMALI_PATH = smali_dir.replace(DECODED_DIR, '')
        break

if ARZ_SMALI_PATH == "":
    raise RuntimeError("❗ Arizona Launcher smali folder not found!")

##################################################################################################################

def patch_smali_method(source, signature, transform):
    pattern = rf"(^\.method [^\n]* {re.escape(signature)}\n)(.*?)(^\.end method$)"
    source, count = re.subn(
        pattern,
        lambda match: match[1] + transform(match[2]) + match[3],
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    if count != 1:
        raise RuntimeError(f"Expected one smali method {signature}, found {count}")
    return source


def inject_before_void_return(body, call):
    return_line = "    return-void\n"
    if return_line not in body:
        raise RuntimeError(f"No return-void found for hook {call}")
    return body.replace(return_line, f"    invoke-static/range {{p0 .. p0}}, {call}\n\n{return_line}")


print("[INFO] 🔧 Injecting Rodina Tools into the launcher lifecycle...")
main_entrench = Path(DECODED_DIR + ARZ_SMALI_PATH) / "com/arizona/launcher/MainEntrench.smali"
main_source = main_entrench.read_text(encoding="utf-8")
for signature, call in (
    ("onCreate(Landroid/os/Bundle;)V", "RodinaTools;->initialize"),
    ("onResume()V", "RodinaTools;->onLauncherResumed"),
    ("onPause()V", "Ads;->onLauncherPaused"),
):
    target = f"Lcom/arizona/launcher/{call}(Landroid/app/Activity;)V"
    main_source = patch_smali_method(
        main_source, signature, lambda body: inject_before_void_return(body, target)
    )
main_entrench.write_text(main_source, encoding="utf-8")

#################################################################################################################

UPDATE_SERVICE_PATH = DECODED_DIR + ARZ_SMALI_PATH + "/com/arizona/launcher/UpdateService.smali"

print("[INFO] 🔒 Disable client updates...")

with open(UPDATE_SERVICE_PATH, "r", encoding="utf-8") as file:
    smali_lines = file.readlines()

matches = [i for i, line in enumerate(smali_lines) if "needUpdateMsg" in line]

if len(matches) != 3:
    print("[INFO] ❌ Unexpected UpdateService structure (needUpdateMsg).")
    print("[INFO] ❌ Client updates not disabled!")
else:
    insert_index = matches[2]
    smali_lines.insert(insert_index + 2, "    const/4 p3, 0x0\n\n")

    with open(UPDATE_SERVICE_PATH, "w", encoding="utf-8") as file:
        file.writelines(smali_lines)

    print("[INFO] ✅ Client updates disabled successfully!")

##################################################################################################################

BG_SRC = Path(PATH) / "background_home.webp"
BG_DEST = Path(DECODED_DIR) / "assets/background_home.webp"

print("[INFO] 🖼️ Pinning the bundled launcher background...")
if BG_SRC.is_file():
    background_class = "com/miami/game/core/design/system/component/background/LauncherBackgroundWriter"
    writers = list(Path(DECODED_DIR).glob(f"smali*/{background_class}.smali"))
    if len(writers) != 1:
        raise RuntimeError(f"Expected one LauncherBackgroundWriter, found {len(writers)}")
    writer = writers[0]
    background = writer.read_text(encoding="utf-8")
    owner = f"L{background_class};"

    # The original writer validates the bundled file and restores it atomically if its hash changed.
    # Bypass the cached remote selection and clean up old downloaded backgrounds in files/launcher_bg.
    local_body = (
        "    .locals 1\n\n"
        f"    invoke-direct {{p0}}, {owner}->ensureValidDefaultFile()Ljava/io/File;\n"
        "    move-result-object v0\n"
        "    if-eqz v0, :return_default\n"
        f"    invoke-direct {{p0}}, {owner}->clearCurrentFile()V\n"
        f"    invoke-direct {{p0, v0}}, {owner}->deleteStaleDownloadedFiles(Ljava/io/File;)V\n"
        "    :return_default\n"
        "    return-object v0\n"
    )
    remote_body = (
        "    .locals 1\n\n"
        "    sget-object v0, Lkotlin/Unit;->INSTANCE:Lkotlin/Unit;\n"
        "    return-object v0\n"
    )
    for dependency in (
        "ensureValidDefaultFile()Ljava/io/File;",
        "clearCurrentFile()V",
        "deleteStaleDownloadedFiles(Ljava/io/File;)V",
    ):
        if not re.search(rf"^\.method private [^\n]*{re.escape(dependency)}$", background, re.MULTILINE):
            raise RuntimeError(f"LauncherBackgroundWriter is missing {dependency}")
    background = patch_smali_method(background, "resolveLocalFile()Ljava/io/File;", lambda _: local_body)
    background = patch_smali_method(
        background, "syncRemoteAndStore(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;",
        lambda _: remote_body,
    )
    BG_DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BG_SRC, BG_DEST)
    # Compose displays these drawables before the writer publishes its first bitmap.
    for project in PROJECTS_APK:
        for fallback in Path(DECODED_DIR).glob(f"res/drawable*/{project}_backgournd_home.webp"):
            shutil.copy2(BG_SRC, fallback)
    writer.write_text(background, encoding="utf-8")
    print("[INFO] ✅ Bundled background pinned")
else:
    print("[INFO] ⚠️ background_home.webp not found in project folder, skipped")

##################################################################################################################

print("[INFO] 🏷️ Changing app name and injecting custom version...")

CUSTOM_VERSION = os.getenv("CUSTOM_VERSION", f"{version_app}.1")

STRINGS_PATH = DECODED_DIR + "/res/values/strings.xml"

if os.path.exists(STRINGS_PATH):
    with open(STRINGS_PATH, "r", encoding="utf-8") as file:
        strings_data = file.read()

    strings_data = re.sub(
        r'(<string name="app_name">)[^<]*(</string>)',
        r'\1Rodina Tools\2',
        strings_data
    )

    if '<string name="custom_version">' in strings_data:
        strings_data = re.sub(r'<string name="custom_version">[^<]*</string>', f'<string name="custom_version">{CUSTOM_VERSION}</string>', strings_data)
    else:
        strings_data = strings_data.replace('</resources>', f'    <string name="custom_version">{CUSTOM_VERSION}</string>\n</resources>')

    with open(STRINGS_PATH, "w", encoding="utf-8") as file:
        file.write(strings_data)

    print(f"[INFO] ✅ App name changed! Custom version: {CUSTOM_VERSION}")
else:
    print("[INFO] ⚠️ strings.xml not found, skipped")

##################################################################################################################

print("[INFO] ⚙️ Rebuilding APK...")
subprocess.run(["java", "-jar", APKTOOL_PATH, "b", DECODED_DIR], check=True)
print("[INFO] ✅ APK rebuilt successfully!")

##################################################################################################################

SIGNED_APK = PATH + f"/{APK_DISPLAY_NAME}.apk"
APKSIGNER_PATH = PATH + "/libs/apksigner.jar"
UNSIGNED_APK = DECODED_DIR + "/dist/" + APK_NAME + ".apk"

KEYSTORE_PATH = PATH + "/gitbuild.jks"
KEY_ALIAS = os.getenv("KEY_ALIAS")
KEY_PASS = os.getenv("KEY_PASS")
KEYSTORE_PASS = os.getenv("KEYSTORE_PASS") or KEY_PASS

if os.path.exists(SIGNED_APK):
    os.remove(SIGNED_APK)

print("[INFO] 🔐 Signing APK...")

if os.path.exists(KEYSTORE_PATH) and KEY_ALIAS and KEY_PASS:
    signing_env = {**os.environ, "RODINA_STORE_PASS": KEYSTORE_PASS, "RODINA_KEY_PASS": KEY_PASS}
    try:
        subprocess.run([
            "java",
            "--enable-native-access=ALL-UNNAMED",
            "-jar",
            APKSIGNER_PATH,
            "sign",
            "--ks", KEYSTORE_PATH,
            "--ks-key-alias", KEY_ALIAS,
            "--ks-pass", "env:RODINA_STORE_PASS",
            "--key-pass", "env:RODINA_KEY_PASS",
            "--out", SIGNED_APK,
            UNSIGNED_APK
        ], check=True, env=signing_env)
        print(f"[INFO] ✅ Signed successfully!")
        print(f"[INFO] ℹ️ Your launcher {version_app}: {SIGNED_APK}")

        idsig = SIGNED_APK + ".idsig"
        if os.path.exists(idsig):
            os.remove(idsig)

    except subprocess.CalledProcessError as e:
        raise RuntimeError("APK signing failed") from e
else:
    print(f"[INFO] ➡️ Signing skipped (no keystore or env vars found)")
    shutil.move(UNSIGNED_APK, SIGNED_APK)
    print(f"[INFO] ℹ️ Your no_signed launcher {version_app}: {SIGNED_APK}")

#################################################################################################################

if version_app != "lua":

    LAUNCHER_JSON_PATH = PATH + "/launcher.json"

    print("[INFO] 📝 Updating launcher.json version...")

    with open(LAUNCHER_JSON_PATH, "r", encoding="utf-8") as file:
        launcher_json = json.load(file)

    version_key = "version" if sys.argv[1] == "arizona" else "rodina_version"

    launcher_json[version_key] = version_app

    with open(LAUNCHER_JSON_PATH, "w", encoding="utf-8") as file:
        json.dump(launcher_json, file, indent=2)

    print(f"[INFO] ✅ Config launcher.json updated: {version_key} = {version_app}")
    
##################################################################################################################

print("[INFO] ✅ Build process completed successfully!")

is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

if not is_github_actions:
    print("[INFO] 🗑️ Remove temporary build directory...")
    shutil.rmtree(DECODED_DIR, ignore_errors=True)
    
##################################################################################################################

