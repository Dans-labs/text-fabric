import sys
import os
import re
from glob import glob

from shutil import rmtree
from subprocess import run, call, Popen, PIPE

import errno
import time
import unicodedata

from tools.pdocs import console, pdoc3serve, pdoc3, shipDocs

ORG = "annotation"
REPO = "text-fabric"
PKG = "tf"
PACKAGE = "text-fabric"
SCRIPT = "/Library/Frameworks/Python.framework/Versions/3.7/bin/{PACKAGE}"

DIST = "dist"

VERSION_CONFIG = dict(
    setup=dict(
        file="setup.py",
        re=re.compile(r"""version\s*=\s*['"]([^'"]*)['"]"""),
        mask="version='{}'",
    ),
    parameters=dict(
        file="tf/parameters.py",
        re=re.compile(r"""\bVERSION\s*=\s*['"]([^'"]*)['"]"""),
        mask="VERSION = '{}'",
    ),
)

AN_BASE = os.path.expanduser(f"~/github/{ORG}")
TUT_BASE = f"{AN_BASE}/tutorials"
TF_BASE = f"{AN_BASE}/{REPO}"
TEST_BASE = f"{TF_BASE}/test"
APP_BASE = f"{TF_BASE}/apps"

SRC = "site"
REMOTE = "origin"
BRANCH = "gh-pages"

currentVersion = None
newVersion = None

appPat = r"^.*/app-([^/]*)$"
appRe = re.compile(appPat)

apps = set()
for appDir in glob(f"{AN_BASE}/app-*"):
    match = appRe.fullmatch(appDir)
    if match:
        apps.add(match.group(1))
apps = sorted(apps)
appStr = ", ".join(apps)

HELP = f"""
python3 build.py command

command:

-h
--help
help  : print help and exit

docs  : serve docs locally
pdocs : build docs
sdocs : ship docs
clean : clean local develop build
l     : local develop build
lp    : local production build
i     : local non-develop build
g     : push to github, code and docs
v     : show current version
r1    : version becomes r1+1.0.0
r2    : version becomes r1.r2+1.0
r3    : version becomes r1.r2.r3+1
ship  : build for shipping
apps  : commit and push all tf apps
tut   : commit and push the tutorials repo
a     : open {PACKAGE} browser on specific dataset
        ({appStr})
t     : run test suite (relations, qperf)
data  : build data files for github release

For g and ship you need to pass a commit message.
For data you need to pass an app argument:
  {appStr}
"""


def readArgs():
    args = sys.argv[1:]
    if not len(args) or args[0] in {"-h", "--help", "help"}:
        console(HELP)
        return (False, None, [])
    arg = args[0]
    if arg not in {
        "a",
        "t",
        "docs",
        "pdocs",
        "sdocs",
        "clean",
        "l",
        "lp",
        "i",
        "g",
        "ship",
        "data",
        "apps",
        "tut",
        "v",
        "r1",
        "r2",
        "r3",
    }:
        console(HELP)
        return (False, None, [])
    if arg in {"g", "apps", "tut", "ship"}:
        if len(args) < 2:
            console("Provide a commit message")
            return (False, None, [])
        return (arg, args[1], args[2:])
    if arg in {"a", "t", "data"}:
        if len(args) < 2:
            if arg in {"a", "data"}:
                console(f"Provide a data source [{appStr}]")
            elif arg in {"t"}:
                console("Provide a test suite [relations, qperf]")
            return (False, None, [])
        return (arg, args[1], args[2:])
    return (arg, None, [])


def incVersion(version, task):
    comps = [int(c) for c in version.split(".")]
    (major, minor, update) = comps
    if task == "r1":
        major += 1
        minor = 0
        update = 0
    elif task == "r2":
        minor += 1
        update = 0
    elif task == "r3":
        update += 1
    return ".".join(str(c) for c in (major, minor, update))


def replaceVersion(task, mask):
    def subVersion(match):
        global currentVersion
        global newVersion
        currentVersion = match.group(1)
        newVersion = incVersion(currentVersion, task)
        return mask.format(newVersion)

    return subVersion


def showVersion():
    global currentVersion
    versions = set()
    for (key, c) in VERSION_CONFIG.items():
        with open(c["file"]) as fh:
            text = fh.read()
        match = c["re"].search(text)
        version = match.group(1)
        console(f'{version} (according to {c["file"]})')
        versions.add(version)
    currentVersion = None
    if len(versions) == 1:
        currentVersion = list(versions)[0]


def adjustVersion(task):
    for (key, c) in VERSION_CONFIG.items():
        console(f'Adjusting version in {c["file"]}')
        with open(c["file"]) as fh:
            text = fh.read()
        text = c["re"].sub(replaceVersion(task, c["mask"]), text)
        with open(c["file"], "w") as fh:
            fh.write(text)
    if currentVersion == newVersion:
        console(f"Rebuilding version {newVersion}")
    else:
        console(f"Replacing version {currentVersion} by {newVersion}")


def makeDist(pypi=True):
    distFile = "{}-{}".format(PACKAGE, currentVersion)
    distFileCompressed = f"{distFile}.tar.gz"
    distPath = f"{DIST}/{distFileCompressed}"
    distPath = f"{DIST}/*"
    print(distPath)
    rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)
    run(["python3", "setup.py", "sdist", "bdist_wheel"])
    if pypi:
        run(["twine", "upload", "-u", "dirkroorda", distPath])
        run("./purge.sh", shell=True)


def commit(task, msg):
    run(["git", "add", "--all", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push", "origin", "master"])
    if task in {"ship"}:
        tagVersion = f"v{currentVersion}"
        commitMessage = f"Release {currentVersion}: {msg}"
        run(["git", "tag", "-a", tagVersion, "-m", commitMessage])
        run(["git", "push", "origin", "--tags"])


def commitApps(msg):
    for app in apps:
        os.chdir(f"{AN_BASE}/app-{app}")
        console(f"In {os.getcwd()}")
        run(["git", "add", "--all", "."])
        run(["git", "commit", "-m", msg])
        run(["git", "push", "origin", "master"])
    os.chdir(f"{TF_BASE}")


def commitTut(msg):
    os.chdir(f"{TUT_BASE}")
    console(f"In {os.getcwd()}")
    run(["git", "add", "--all", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push", "origin", "master"])
    os.chdir(f"{TF_BASE}")


if sys.version_info[0] == 3:

    def enc(text):
        if isinstance(text, bytes):
            return text
        return text.encode()

    def dec(text):
        if isinstance(text, bytes):
            return text.decode("utf-8")
        return text

    def write(pipe, data):
        try:
            pipe.stdin.write(data)
        except OSError as e:
            if e.errno != errno.EPIPE:
                raise


else:

    def enc(text):
        if isinstance(text, unicode):  # noqa: F821
            return text.encode("utf-8")
        return text

    def dec(text):
        if isinstance(text, unicode):  # noqa: F821
            return text
        return text.decode("utf-8")

    def write(pipe, data):
        pipe.stdin.write(data)


# COPIED FROM MKDOCS AND MODIFIED


def normalize_path(path):
    # Fix unicode pathnames on OS X
    # See: https://stackoverflow.com/a/5582439/44289
    if sys.platform == "darwin":
        return unicodedata.normalize("NFKC", dec(path))
    return path


def try_rebase(remote, branch):
    cmd = ["git", "rev-list", "--max-count=1", "{}/{}".format(remote, branch)]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (rev, _) = p.communicate()
    if p.wait() != 0:
        return True
    cmd = ["git", "update-ref", "refs/heads/%s" % branch, dec(rev.strip())]
    if call(cmd) != 0:
        return False
    return True


def get_config(key):
    p = Popen(["git", "config", key], stdin=PIPE, stdout=PIPE)
    (value, _) = p.communicate()
    return value.decode("utf-8").strip()


def get_prev_commit(branch):
    cmd = ["git", "rev-list", "--max-count=1", branch, "--"]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (rev, _) = p.communicate()
    if p.wait() != 0:
        return None
    return rev.decode("utf-8").strip()


def mk_when(timestamp=None):
    if timestamp is None:
        timestamp = int(time.time())
    currtz = "%+05d" % (-1 * time.timezone / 36)  # / 3600 * 100
    return "{} {}".format(timestamp, currtz)


def start_commit(pipe, branch, message):
    uname = dec(get_config("user.name"))
    email = dec(get_config("user.email"))
    write(pipe, enc("commit refs/heads/%s\n" % branch))
    write(pipe, enc("committer {} <{}> {}\n".format(uname, email, mk_when())))
    write(pipe, enc("data %d\n%s\n" % (len(message), message)))
    head = get_prev_commit(branch)
    if head:
        write(pipe, enc("from %s\n" % head))
    write(pipe, enc("deleteall\n"))


def add_file(pipe, srcpath, tgtpath):
    with open(srcpath, "rb") as handle:
        if os.access(srcpath, os.X_OK):
            write(pipe, enc("M 100755 inline %s\n" % tgtpath))
        else:
            write(pipe, enc("M 100644 inline %s\n" % tgtpath))
        data = handle.read()
        write(pipe, enc("data %d\n" % len(data)))
        write(pipe, enc(data))
        write(pipe, enc("\n"))


def add_nojekyll(pipe):
    write(pipe, enc("M 100644 inline .nojekyll\n"))
    write(pipe, enc("data 0\n"))
    write(pipe, enc("\n"))


def gitpath(fname):
    norm = os.path.normpath(fname)
    return "/".join(norm.split(os.path.sep))


def ghp_import():
    if not try_rebase(REMOTE, BRANCH):
        print("Failed to rebase %s branch.", BRANCH)

    console("copy docs to the gh-pages branch")
    cmd = ["git", "fast-import", "--date-format=raw", "--quiet"]
    kwargs = {"stdin": PIPE}
    if sys.version_info >= (3, 2, 0):
        kwargs["universal_newlines"] = False
    pipe = Popen(cmd, **kwargs)
    start_commit(pipe, BRANCH, "docs update")
    for path, _, fnames in os.walk(SRC):
        for fn in fnames:
            fpath = os.path.join(path, fn)
            fpath = normalize_path(fpath)
            gpath = gitpath(os.path.relpath(fpath, start=SRC))
            add_file(pipe, fpath, gpath)
    add_nojekyll(pipe)
    write(pipe, enc("\n"))
    pipe.stdin.close()
    if pipe.wait() != 0:
        sys.stdout.write(enc("Failed to process commit.\n"))

    console("push gh-pages branch to GitHub")
    cmd = ["git", "push", REMOTE, BRANCH]
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    (out, err) = proc.communicate()
    result = proc.wait() == 0

    return result, dec(err)


# END COPIED FROM MKDOCS AND MODIFIED


def tfbrowse(dataset, remaining):
    rargs = " ".join(remaining)
    cmdLine = f"{PACKAGE} {dataset} {rargs}"
    try:
        run(cmdLine, shell=True)
    except KeyboardInterrupt:
        pass


def tftest(suite, remaining):
    suiteDir = f"{TEST_BASE}/generic"
    suiteFile = f"{suite}.py"
    good = True
    try:
        os.chdir(suiteDir)
    except Exception:
        good = False
        console(f'Cannot find TF test directory "{suiteDir}"')
    if not good:
        return
    if not os.path.exists(suiteFile):
        console(f'Cannot find TF test suite "{suite}"')
        return
    rargs = " ".join(remaining)
    cmdLine = f"python3 {suiteFile} -v {rargs}"
    try:
        run(cmdLine, shell=True)
    except KeyboardInterrupt:
        pass


def clean():
    run(["python3", "setup.py", "develop", "-u"])
    if os.path.exists(SCRIPT):
        os.unlink(SCRIPT)
    run(["pip3", "uninstall", "-y", PACKAGE])


def main():
    (task, msg, remaining) = readArgs()
    if not task:
        return
    elif task == "a":
        tfbrowse(msg, remaining)
    elif task == "t":
        tftest(msg, remaining)
    elif task == "docs":
        pdoc3serve(PKG)
    elif task == "pdocs":
        pdoc3(PKG)
    elif task == "sdocs":
        shipDocs(ORG, REPO, PKG)
    elif task == "clean":
        clean()
    elif task == "l":
        clean()
        run(["python3", "setup.py", "develop"])
    elif task == "lp":
        clean()
        run(["python3", "setup.py", "sdist"])
        distFiles = glob(f"dist/{PACKAGE}-*.tar.gz")
        run(["pip3", "install", distFiles[0]])
    elif task == "i":
        clean
        makeDist(pypi=False)
        run(
            [
                "pip3",
                "install",
                "--upgrade",
                "--no-index",
                "--find-links",
                f'file://{TF_BASE}/dist"',
                PACKAGE,
            ]
        )
    elif task == "g":
        shipDocs(ORG, REPO, PKG)
        commit(task, msg)
    elif task == "apps":
        commitApps(msg)
    elif task == "tut":
        commitTut(msg)
    elif task == "v":
        showVersion()
    elif task in {"r", "r1", "r2", "r3"}:
        adjustVersion(task)
    elif task == "ship":
        showVersion()
        if not currentVersion:
            console("No current version")
            return

        answer = input("right version ? [yn]")
        if answer != "y":
            return
        shipDocs(ORG, REPO, PKG)
        makeDist()
        commit(task, msg)


main()
