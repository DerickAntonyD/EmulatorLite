from fastapi import FastAPI
from fastapi.responses import FileResponse, Response, JSONResponse
from pathlib import Path
from fastapi import UploadFile, File
from pydantic import BaseModel
import subprocess
import time
import os
import shutil


app = FastAPI()


# ============================================================
# PLATFORM / PATH CONFIGURATION
# ============================================================

# Project folder
BASE = Path(__file__).resolve().parent


# Find ADB automatically.
#
# LOCAL WINDOWS:
# Uses your Android SDK ADB.
#
# RENDER / LINUX:
# ADB will normally not exist, so ADB features will be
# unavailable instead of crashing the whole FastAPI server.

WINDOWS_ADB = Path(
    r"D:\androisemulatsetupsmallphoner\platform-tools\adb.exe"
)

if WINDOWS_ADB.exists():
    ADB = str(WINDOWS_ADB)
else:
    ADB = shutil.which("adb")


IS_EMULATOR_AVAILABLE = ADB is not None


# AAPT2 is only needed for APK analysis.
WINDOWS_AAPT2 = Path(
    r"D:\androisemulatsetupsmallphoner\build-tools\36.0.0\aapt2.exe"
)

if WINDOWS_AAPT2.exists():
    AAPT2 = str(WINDOWS_AAPT2)
else:
    AAPT2 = shutil.which("aapt2")


# ============================================================
# ADB HELPER
# ============================================================

def run_adb(*args):

    result = subprocess.run(
        [ADB, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10
    )

    if result.returncode != 0:

        error = result.stderr.decode(
            errors="replace"
        )

        raise RuntimeError(
            error or "ADB command failed"
        )

    return result


# ============================================================
# SCREEN CAPTURE
# ============================================================

def capture_screen():

    result = run_adb(
        "exec-out",
        "screencap",
        "-p"
    )

    if not result.stdout.startswith(
        b"\x89PNG"
    ):
        raise RuntimeError(
            "Invalid PNG returned by Android"
        )

    return result.stdout


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        BASE / "index.html"
    )


# ============================================================
# SCREEN
# ============================================================

@app.get("/screen")
def screen():

    try:

        image = capture_screen()

        return Response(
            content=image,
            media_type="image/png",
            headers={
                "Cache-Control": "no-store"
            }
        )

    except Exception as e:

        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": str(e)
            }
        )


# ============================================================
# EMULATOR STATUS
# ============================================================

@app.get("/status")
def status():

    try:

        result = run_adb(
            "get-state"
        )

        state = result.stdout.decode().strip()

        return {
            "ok": state == "device",
            "adb_state": state,
            "time": time.time()
        }

    except Exception as e:

        return {
            "ok": False,
            "error": str(e)
        }


# ============================================================
# NAVIGATION CONTROLS
# ============================================================

@app.post("/control/{action}")
def control(action: str):

    commands = {

        "back": [
            "shell",
            "input",
            "keyevent",
            "4"
        ],

        "home": [
            "shell",
            "input",
            "keyevent",
            "3"
        ],

        "recents": [
            "shell",
            "input",
            "keyevent",
            "187"
        ]

    }

    if action not in commands:

        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "Unknown action"
            }
        )

    try:

        run_adb(
            *commands[action]
        )

        return {
            "ok": True,
            "action": action
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )


# ============================================================
# TAP
# ============================================================

class TapRequest(BaseModel):

    x: int
    y: int


@app.post("/tap")
def tap(request: TapRequest):

    try:

        run_adb(
            "shell",
            "input",
            "tap",
            str(request.x),
            str(request.y)
        )

        return {
            "ok": True,
            "x": request.x,
            "y": request.y
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )


# ============================================================
# SWIPE
# ============================================================

class SwipeRequest(BaseModel):

    x1: int
    y1: int

    x2: int
    y2: int

    duration: int = 300


@app.post("/swipe")
def swipe(request: SwipeRequest):

    try:

        run_adb(
            "shell",
            "input",
            "swipe",

            str(request.x1),
            str(request.y1),

            str(request.x2),
            str(request.y2),

            str(request.duration)
        )

        return {

            "ok": True,

            "x1": request.x1,
            "y1": request.y1,

            "x2": request.x2,
            "y2": request.y2,

            "duration": request.duration

        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )

# ============================================================
# TEXT INPUT
# ============================================================

class TextRequest(BaseModel):

    text: str


@app.post("/text")
def text_input(request: TextRequest):

    try:

        # Escape characters that ADB input text
        # treats specially.

        text = request.text

        text = text.replace(
            " ",
            "%s"
        )

        text = text.replace(
            "&",
            "\\&"
        )

        text = text.replace(
            ";",
            "\\;"
        )

        text = text.replace(
            "|",
            "\\|"
        )

        text = text.replace(
            "<",
            "\\<"
        )

        text = text.replace(
            ">",
            "\\>"
        )

        text = text.replace(
            "(",
            "\\("
        )

        text = text.replace(
            ")",
            "\\)"
        )

        run_adb(
            "shell",
            "input",
            "text",
            text
        )

        return {
            "ok": True,
            "text": request.text
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )

# ============================================================
# TEXT INPUT
# ============================================================

class TextRequest(BaseModel):

    text: str


@app.post("/text")
def text_input(request: TextRequest):

    try:

        text = request.text

        # Android ADB text escaping
        text = text.replace(" ", "%s")
        text = text.replace("&", "\\&")
        text = text.replace(";", "\\;")
        text = text.replace("|", "\\|")
        text = text.replace("<", "\\<")
        text = text.replace(">", "\\>")
        text = text.replace("(", "\\(")
        text = text.replace(")", "\\)")

        run_adb(
            "shell",
            "input",
            "text",
            text
        )

        return {
            "ok": True,
            "text": request.text
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )

# ============================================================
# EMULATOR COMPATIBILITY CHECK
# ============================================================

@app.get("/compatibility")
def compatibility():

    PACKAGE = "com.neonrunblza.game"

    try:

        # ----------------------------------------------------
        # Android version
        # ----------------------------------------------------

        android_version = run_adb(
            "shell",
            "getprop",
            "ro.build.version.release"
        ).stdout.decode().strip()

        # ----------------------------------------------------
        # Android API level
        # ----------------------------------------------------

        api_level_text = run_adb(
            "shell",
            "getprop",
            "ro.build.version.sdk"
        ).stdout.decode().strip()

        api_level = int(api_level_text)

        # ----------------------------------------------------
        # Google Play Services
        # ----------------------------------------------------

        play_services = run_adb(
            "shell",
            "pm",
            "path",
            "com.google.android.gms"
        ).returncode == 0

        # ----------------------------------------------------
        # Google AdServices
        # ----------------------------------------------------

        adservices = run_adb(
            "shell",
            "pm",
            "path",
            "com.google.android.adservices.api"
        ).returncode == 0

        # ----------------------------------------------------
        # APK package information
        # ----------------------------------------------------

        package_output = run_adb(
            "shell",
            "dumpsys",
            "package",
            PACKAGE
        ).stdout.decode(
            errors="replace"
        )

        version_name = "Unknown"
        version_code = None
        min_sdk = None
        target_sdk = None

        for line in package_output.splitlines():

            line = line.strip()

            if line.startswith("versionName="):

                version_name = (
                    line.split(
                        "=",
                        1
                    )[1]
                    .strip()
                )

            elif "versionCode=" in line:

                parts = line.split()

                for part in parts:

                    if part.startswith(
                        "versionCode="
                    ):

                        version_code = int(
                            part.split(
                                "=",
                                1
                            )[1]
                        )

                    elif part.startswith(
                        "minSdk="
                    ):

                        min_sdk = int(
                            part.split(
                                "=",
                                1
                            )[1]
                        )

                    elif part.startswith(
                        "targetSdk="
                    ):

                        target_sdk = int(
                            part.split(
                                "=",
                                1
                            )[1]
                        )

        # ----------------------------------------------------
        # Runtime compatibility
        # ----------------------------------------------------

        compatible = (
            min_sdk is not None
            and
            api_level >= min_sdk
        )

        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return {

            "ok": True,

            "android_version":
                android_version,

            "api_level":
                api_level,

            "google_play_services":
                play_services,

            "google_adservices":
                adservices,

            "package":
                PACKAGE,

            "version":
                version_name,

            "version_code":
                version_code,

            "min_sdk":
                min_sdk,

            "target_sdk":
                target_sdk,

            "compatible":
                compatible

        }

    except Exception as e:

        return JSONResponse(

            status_code=500,

            content={

                "ok": False,

                "error": str(e)

            }

        )

# ============================================================
# LAUNCH GAME
# ============================================================

@app.post("/launch-game")
def launch_game():

    PACKAGE = "com.neonrunblza.game"

    try:

        run_adb(
            "shell",
            "monkey",
            "-p",
            PACKAGE,
            "1"
        )

        return {

            "ok": True,

            "package": PACKAGE,

            "message": "Game launched"

        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )

# ============================================================
# APK UPLOAD
# ============================================================

UPLOAD_DIR = BASE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/upload-apk")
async def upload_apk(file: UploadFile = File(...)):

    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "No APK selected"
            }
        )

    if not file.filename.lower().endswith(".apk"):
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "Only .apk files are allowed"
            }
        )

    filename = Path(file.filename).name
    apk_path = UPLOAD_DIR / filename

    with open(apk_path, "wb") as output:

        while True:

            chunk = await file.read(1024 * 1024)

            if not chunk:
                break

            output.write(chunk)

    return {
        "ok": True,
        "filename": filename,
        "path": str(apk_path),
        "size": apk_path.stat().st_size
    }

# ============================================================
# APK ANALYZER
# ============================================================
@app.get("/analyze-apk")
def analyze_apk():

    apk_files = list(UPLOAD_DIR.glob("*.apk"))

    if not apk_files:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "No APK found in uploads folder"
            }
        )

    # Use the newest APK
    apk_path = max(apk_files, key=lambda p: p.stat().st_mtime)

    AAPT2 = r"D:\androisemulatsetupsmallphoner\build-tools\36.0.0\aapt2.exe"

    try:

        result = subprocess.run(
            [
                AAPT2,
                "dump",
                "badging",
                str(apk_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        output = result.stdout.decode(
            "utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            error = result.stderr.decode(
                "utf-8",
                errors="replace"
            )

            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "APK analysis failed",
                    "details": error
                }
            )

        # Default values
        package_name = None
        version_name = None
        version_code = None
        min_sdk = None
        target_sdk = None
        app_name = None
        launchable_activity = None
        compile_sdk = None

        # Parse package information
        for line in output.splitlines():

            line = line.strip()

            if line.startswith("package:"):

                parts = line.split()

                for part in parts:

                    if part.startswith("name="):
                        package_name = part.split(
                            "=", 1
                        )[1].strip("'")

                    elif part.startswith("versionCode="):
                        version_code = part.split(
                            "=", 1
                        )[1].strip("'")

                    elif part.startswith("versionName="):
                        version_name = part.split(
                            "=", 1
                        )[1].strip("'")

                    elif part.startswith("compileSdkVersion="):
                        compile_sdk = part.split(
                            "=", 1
                        )[1].strip("'")

            elif line.startswith("minSdkVersion:"):
                min_sdk = line.split(
                    ":", 1
                )[1].strip("'")

            elif line.startswith("targetSdkVersion:"):
                target_sdk = line.split(
                    ":", 1
                )[1].strip("'")

            elif line.startswith("application-label:"):
                app_name = line.split(
                    ":", 1
                )[1].strip("'")

            elif line.startswith("launchable-activity:"):
                activity_part = line.split(
                    "name=",
                    1
                )

                if len(activity_part) > 1:
                    launchable_activity = activity_part[1].split(
                        " ",
                        1
                    )[0]

                    launchable_activity = (
                        launchable_activity
                        .strip("'")
                    )

        # Emulator API level
        emulator_api = int(
            run_adb(
                "shell",
                "getprop",
                "ro.build.version.sdk"
            ).stdout.decode().strip()
        )

        # Compatibility check
        compatible = (
            min_sdk is not None
            and emulator_api >= int(min_sdk)
        )

        return {
            "ok": True,

            "apk": apk_path.name,
            "size": apk_path.stat().st_size,

            "app_name": app_name,
            "package": package_name,

            "version": version_name,
            "version_code": (
                int(version_code)
                if version_code
                else None
            ),

            "min_sdk": (
                int(min_sdk)
                if min_sdk
                else None
            ),

            "target_sdk": (
                int(target_sdk)
                if target_sdk
                else None
            ),

            "compile_sdk": (
                int(compile_sdk)
                if compile_sdk
                else None
            ),

            "launchable_activity": launchable_activity,

            "emulator": {
                "android_api": emulator_api
            },

            "compatible": compatible
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )

@app.post("/install-apk")
def install_apk():

    apk_files = list(UPLOAD_DIR.glob("*.apk"))

    if not apk_files:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "No APK found in uploads folder"
            }
        )

    # Use newest uploaded APK
    apk_path = max(
        apk_files,
        key=lambda p: p.stat().st_mtime
    )

    try:

        result = subprocess.run(
            [
                ADB,
                "install",
                "-r",
                str(apk_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        stdout = result.stdout.decode(
            "utf-8",
            errors="replace"
        ).strip()

        stderr = result.stderr.decode(
            "utf-8",
            errors="replace"
        ).strip()

        if result.returncode != 0:

            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "apk": apk_path.name,
                    "error": stderr or stdout or "APK installation failed"
                }
            )

        return {
            "ok": True,
            "apk": apk_path.name,
            "message": "APK installed successfully",
            "output": stdout
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )


@app.post("/launch-apk")
def launch_apk():

    apk_files = list(UPLOAD_DIR.glob("*.apk"))

    if not apk_files:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "No APK found in uploads folder"
            }
        )

    apk_path = max(
        apk_files,
        key=lambda p: p.stat().st_mtime
    )

    AAPT2 = r"D:\androisemulatsetupsmallphoner\build-tools\36.0.0\aapt2.exe"

    try:

        # Analyze APK
        result = subprocess.run(
            [
                AAPT2,
                "dump",
                "badging",
                str(apk_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        output = result.stdout.decode(
            "utf-8",
            errors="replace"
        )

        package_name = None
        launchable_activity = None

        for line in output.splitlines():

            line = line.strip()

            if line.startswith("package:"):

                for part in line.split():

                    if part.startswith("name="):
                        package_name = part.split(
                            "=", 1
                        )[1].strip("'")

            elif line.startswith("launchable-activity:"):

                if "name=" in line:

                    launchable_activity = (
                        line.split("name=", 1)[1]
                        .split(" ", 1)[0]
                        .strip("'")
                    )

        if not package_name:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "Could not detect APK package"
                }
            )

        if not launchable_activity:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "Could not detect launchable activity",
                    "package": package_name
                }
            )

        # Launch detected activity
        launch = run_adb(
            "shell",
            "am",
            "start",
            "-n",
            f"{package_name}/{launchable_activity}"
        )

        return {
            "ok": True,
            "apk": apk_path.name,
            "package": package_name,
            "activity": launchable_activity,
            "message": "APK launched successfully",
            "output": launch.stdout.decode(
                "utf-8",
                errors="replace"
            ).strip()
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )