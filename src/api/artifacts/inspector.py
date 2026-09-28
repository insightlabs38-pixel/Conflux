"""Safe, static inspection of submitted artifacts (PVS08).

Nothing here executes, renders or extracts content: it reads bytes, parses
headers and archive directories, and reports what a reviewer should know
before opening a file. Every reported value is data, never markup.
"""

import hashlib
import io
import re
import struct
import zipfile
from dataclasses import dataclass, field

INSPECTOR_VERSION = "1"
MAX_INSPECT_BYTES = 25 * 1024 * 1024
MAX_ZIP_ENTRIES = 10_000
MAX_ZIP_EXPANSION = 1024 * 1024 * 1024
MAX_ZIP_RATIO = 200
MAX_IMAGE_PIXELS = 178_956_970
PREVIEW_CHARS = 4000
LISTED_ENTRIES = 50

EXECUTABLE_MAGIC = (
    (b"MZ", "Windows executable"),
    (b"\x7fELF", "Linux executable"),
    (b"\xcf\xfa\xed\xfe", "macOS executable"),
    (b"\xce\xfa\xed\xfe", "macOS executable"),
    (b"\xca\xfe\xba\xbe", "macOS/Java executable"),
    (b"#!", "script with an interpreter line"),
)
EXECUTABLE_SUFFIXES = (
    ".exe", ".dll", ".msi", ".scr", ".bat", ".cmd", ".com", ".sh", ".app", ".jar", ".ps1",
    ".vbs", ".js", ".apk", ".dmg", ".pkg", ".lnk",
)  # fmt: skip
ARCHIVE_SUFFIXES = (".zip", ".jar", ".war", ".7z", ".rar", ".tar", ".gz", ".tgz")
SECRET_PATTERNS = (
    ("private key block", re.compile(rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY")),
    ("AWS access key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("API secret key", re.compile(rb"\bsk-[A-Za-z0-9]{32,}\b")),
    ("Google API key", re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b")),
)
FAMILY = {
    "image": {"png", "jpeg", "gif", "webp"},
    "video": {"mp4"},
    "document": {"pdf", "text"},
    "dataset": {"text", "zip", "gzip"},
    "file": None,
    "secret": None,
}


@dataclass
class Inspection:
    detected_type: str = "unknown"
    findings: list = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    preview: str = ""

    def add(self, severity, code, detail):
        self.findings.append({"severity": severity, "code": code, "detail": detail})

    @property
    def verdict(self):
        severities = {f["severity"] for f in self.findings}
        return (
            "blocked"
            if "blocked" in severities
            else "warnings"
            if "warning" in severities
            else "clean"
        )

    def as_dict(self):
        return {
            "verdict": self.verdict,
            "detected_type": self.detected_type,
            "findings": self.findings,
            "facts": self.facts,
            "preview": self.preview,
            "inspector_version": INSPECTOR_VERSION,
        }


def sniff(head):
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        return "zip"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    if head[4:8] == b"ftyp":
        return "mp4"
    for magic, _ in EXECUTABLE_MAGIC:
        if head.startswith(magic):
            return "executable"
    stripped = head.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if stripped.startswith((b"<!doctype html", b"<html", b"<script", b"<iframe")):
        return "html"
    if stripped.startswith((b"<svg", b"<?xml")) and b"<svg" in head.lower():
        return "svg"
    if b"\x00" not in head:
        try:
            head.decode("utf-8")
        except UnicodeDecodeError:
            return "binary"
        return "text"
    return "binary"


def _image_size(kind, data):
    try:
        if kind == "png":
            return struct.unpack(">II", data[16:24])
        if kind == "gif":
            return struct.unpack("<HH", data[6:10])
        if kind == "webp":
            chunk = data[12:16]
            if chunk == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                return w & 0x3FFF, h & 0x3FFF
            if chunk == b"VP8L":
                bits = struct.unpack("<I", data[21:25])[0]
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            if chunk == b"VP8X":
                return (
                    int.from_bytes(data[24:27], "little") + 1,
                    int.from_bytes(data[27:30], "little") + 1,
                )
        if kind == "jpeg":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                length = struct.unpack(">H", data[i + 2 : i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    return w, h
                i += 2 + length
    except (struct.error, IndexError):
        return None
    return None


def _inspect_image(kind, data, report):
    size = _image_size(kind, data)
    if size is None:
        report.add("warning", "image_unreadable", "The image header could not be read.")
        return
    width, height = size
    report.facts.update({"width": width, "height": height})
    if width == 0 or height == 0 or width * height > MAX_IMAGE_PIXELS:
        report.add("warning", "image_dimensions", f"Unusual image size {width}x{height}.")
    if kind == "jpeg" and b"Exif\x00\x00" in data[:65536]:
        report.add(
            "warning",
            "image_metadata",
            "Camera metadata (EXIF) is present and may reveal a location.",
        )


def _inspect_pdf(data, report):
    pages = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", data))
    report.facts["pages"] = pages
    for token, message in (
        (b"/JavaScript", "The PDF contains JavaScript."),
        (b"/JS", "The PDF contains JavaScript."),
        (b"/OpenAction", "The PDF runs an action when opened."),
        (b"/Launch", "The PDF can launch other programs."),
        (b"/EmbeddedFile", "The PDF embeds other files."),
    ):
        if token in data:
            report.add("warning", "pdf_active_content", message)
            break
    if b"/Encrypt" in data:
        report.add("warning", "pdf_encrypted", "The PDF is encrypted and cannot be checked.")


def _inspect_zip(source, report):
    try:
        archive = zipfile.ZipFile(source)
    except (zipfile.BadZipFile, ValueError, OSError):
        report.add("warning", "archive_unreadable", "The archive directory could not be read.")
        return
    with archive:
        entries = archive.infolist()
        report.facts["entries"] = len(entries)
        if len(entries) > MAX_ZIP_ENTRIES:
            report.add("blocked", "archive_entries", f"More than {MAX_ZIP_ENTRIES} entries.")
            return
        total = sum(e.file_size for e in entries)
        packed = sum(e.compress_size for e in entries) or 1
        report.facts.update({"uncompressed_bytes": total, "compressed_bytes": packed})
        if total > MAX_ZIP_EXPANSION or total / packed > MAX_ZIP_RATIO and total > 10 * 1024 * 1024:
            report.add(
                "blocked",
                "archive_bomb",
                f"Expands to {total} bytes from {packed}; treat as a decompression bomb.",
            )
        unsafe = [
            e.filename
            for e in entries
            if e.filename.startswith(("/", "\\"))
            or ".." in re.split(r"[\\/]", e.filename)
            or re.match(r"^[A-Za-z]:", e.filename)
        ]
        if unsafe:
            report.add(
                "blocked", "archive_path_traversal", f"{len(unsafe)} entries escape their folder."
            )
        if any(e.flag_bits & 0x1 for e in entries):
            report.add("warning", "archive_encrypted", "Some entries are password protected.")
        if any((e.external_attr >> 16) & 0o170000 == 0o120000 for e in entries):
            report.add("warning", "archive_symlinks", "The archive contains symbolic links.")
        programs = [e.filename for e in entries if e.filename.lower().endswith(EXECUTABLE_SUFFIXES)]
        if programs:
            report.add(
                "warning", "archive_programs", f"{len(programs)} program or script files inside."
            )
        nested = [e.filename for e in entries if e.filename.lower().endswith(ARCHIVE_SUFFIXES)]
        if nested:
            report.add("warning", "archive_nested", f"{len(nested)} archives inside the archive.")
        secrets = [
            e.filename
            for e in entries
            if re.search(
                r"(^|/)(\.env(\..*)?|id_rsa|id_ed25519|.*\.pem|.*\.p12|credentials(\.json)?)$",
                e.filename,
            )
        ]
        if secrets:
            report.add(
                "warning", "archive_secret_files", f"{len(secrets)} files look like credentials."
            )
        report.facts["listing"] = [
            {"name": e.filename[:200], "size": e.file_size} for e in entries[:LISTED_ENTRIES]
        ]


def _scan_secrets(data, report):
    for label, pattern in SECRET_PATTERNS:
        match = pattern.search(data)
        if match:
            line = data[: match.start()].count(b"\n") + 1
            report.add("warning", "possible_secret", f"A {label} appears near line {line}.")


def _printable(text):
    return "".join(ch if ch in "\n\t" or ch.isprintable() else "�" for ch in text)


def _redact_secrets(data):
    for _, pattern in SECRET_PATTERNS:
        data = pattern.sub(b"[redacted]", data)
    return data


def inspect_bytes(data, *, claimed_type="", filename="", kind="file", expected_sha256=""):
    report = Inspection()
    report.facts["bytes"] = len(data)
    report.facts["sha256"] = hashlib.sha256(data).hexdigest()
    if expected_sha256 and expected_sha256 != report.facts["sha256"]:
        report.add(
            "blocked", "digest_mismatch", "The content does not match the recorded checksum."
        )
    detected = sniff(data[:4096])
    report.detected_type = detected
    claimed = claimed_type.split(";", 1)[0].strip().lower()
    if detected in ("html", "svg"):
        report.add("blocked", "active_content", "The file is web content that can run scripts.")
    if detected == "executable":
        report.add("blocked", "executable", "The file is a program, not a document or media file.")
    allowed = FAMILY.get(kind)
    if (
        allowed is not None
        and detected not in allowed
        and detected not in ("html", "svg", "executable")
    ):
        report.add(
            "warning",
            "type_mismatch",
            f"Submitted as {kind} but the content looks like {detected}.",
        )
    if claimed and detected not in ("binary", "text", "unknown"):
        family = claimed.split("/")[0]
        if (
            (family == "image" and detected not in FAMILY["image"])
            or (claimed == "application/pdf" and detected != "pdf")
            or (family == "video" and detected != "mp4")
        ):
            report.add(
                "warning",
                "claimed_type_mismatch",
                f"Declared {claimed} but the content looks like {detected}.",
            )
    if filename.lower().endswith(EXECUTABLE_SUFFIXES) and detected != "executable":
        report.add("warning", "program_extension", "The file name looks like a program or script.")
    if detected in FAMILY["image"]:
        _inspect_image(detected, data, report)
    elif detected == "pdf":
        _inspect_pdf(data, report)
    elif detected == "zip":
        _inspect_zip(io.BytesIO(data), report)
    if detected in ("text", "html", "svg", "binary", "zip", "pdf"):
        _scan_secrets(data[:2_000_000], report)
    if detected == "text":
        redacted = _redact_secrets(data[: PREVIEW_CHARS * 4])
        report.preview = _printable(redacted.decode("utf-8", "replace"))[:PREVIEW_CHARS]
    return report
