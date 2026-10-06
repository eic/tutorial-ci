#!/usr/bin/env python3
"""Check that every xrootd path and rucio DID quoted in a tutorial is still available.

Usage: check_paths.py <tutorial directory>
"""
import re
import sys
from pathlib import Path

from XRootD import client
from rucio.client import Client

URL = re.compile(r"(root://[\w.\-]+(?::\d+)?)/(/[^\s\"'`()<>\[\]]*)")
XRDFS = re.compile(r"xrdfs (root://[\w.\-]+(?::\d+)?)(?: (?:ls|cat|stat) (/[^\s\"'`|]*))?")
LS = re.compile(r"^\s*ls (/[^\s\"'`|]*)")
DID = re.compile(r"\bepic:(/[^\s\"'`()<>\[\]]+)")
PLACEHOLDERS = ("path-to-file", "<", "{", "...", "…", "*")
SUFFIXES = (".md", ".Rmd", ".py", ".C", ".cxx", ".sh", ".ipynb", ".yaml", ".yml", ".config", "Snakefile")


def references(directory):
    """Yield (file, line number, kind, server, path) for each quoted path."""
    for file in sorted(Path(directory).rglob("*")):
        if ".git" in file.parts or not file.is_file() or not file.name.endswith(SUFFIXES):
            continue
        server = None  # set by a bare `xrdfs root://server` line, used by following `ls /path` lines
        for number, line in enumerate(file.read_text(errors="ignore").splitlines(), 1):
            for match in XRDFS.finditer(line):
                server = match.group(1)
                if match.group(2):
                    yield file, number, "xrootd", server, match.group(2)
            if not XRDFS.search(line):
                for match in URL.finditer(line):
                    yield file, number, "xrootd", match.group(1), match.group(2)
            match = LS.match(line)
            if match and server:
                yield file, number, "xrootd", server, match.group(1)
            for match in DID.finditer(line):
                yield file, number, "rucio", None, match.group(1)


def clean(path):
    return path.rstrip(".,;:")


def xrootd_exists(server, path):
    status, _ = client.FileSystem(server).stat(path, timeout=60)
    return status.ok, status.message


def rucio_open_access(name):
    """True if the DID has at least one replica on an open-access storage element."""
    try:
        replicas = Client().list_replicas([{"scope": "epic", "name": name.rstrip("/")}], rse_expression="isopenaccess")
        return any(replica["rses"] for replica in replicas), "no open-access replica"
    except Exception as error:
        return False, type(error).__name__


def main(directory):
    results = {}
    failures = 0
    for file, number, kind, server, path in references(directory):
        if any(placeholder in path for placeholder in PLACEHOLDERS):
            continue
        path = clean(path)
        key = (kind, server, path)
        if key not in results:
            results[key] = xrootd_exists(server, path) if kind == "xrootd" else rucio_open_access(path)
        ok, message = results[key]
        location = f"{file.relative_to(directory)}:{number}"
        target = f"{server}/{path}" if server else f"epic:{path}"
        if ok:
            print(f"OK      {location}  {target}")
        else:
            failures += 1
            print(f"MISSING {location}  {target}  ({message.strip()})")
            print(f"::error file={file.relative_to(directory)},line={number}::{target} not available ({message.strip()})")
    print(f"{len(results)} unique references, {failures} missing")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
