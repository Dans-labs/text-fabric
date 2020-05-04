import re
import types

from ..parameters import URL_GH, URL_NB, URL_TFDOC
from ..core.helpers import console, mdEsc
from .displaysettings import INTERFACE_OPTIONS
from .helpers import dm


VAR_PATTERN = re.compile(r"\{([^}]+)\}")

WRITING_DEFAULTS = dict(
    akk=dict(
        language="Akkadian",
        fontName="Santakku",
        font="Santakk.ttf",
        fontw="Santakku.woff",
        direction="ltr",
    ),
    hbo=dict(
        language="Hebrew",
        fontName="Ezra SIL",
        font="SILEOT.ttf",
        fontw="SILEOT.woff",
        direction="rtl",
    ),
    syc=dict(
        language="Syriac",
        fontName="Estrangelo Edessa",
        font="SyrCOMEdessa.otf",
        fontw="SyrCOMEdessa.woff",
        direction="rtl",
    ),
    ara=dict(
        language="Arabic",
        fontName="AmiriQuran",
        font="AmiriQuran.ttf",
        fontw="AmiriQuran.woff2",
        direction="rtl",
    ),
    grc=dict(
        language="Greek",
        fontName="Gentium",
        font="GentiumPlus-R.ttf",
        fontw="GentiumPlus-R.woff",
        direction="ltr",
    ),
    cld=dict(
        language="Aramaic",
        fontName="CharisSIL-R",
        font="CharisSIL-R.otf",
        fontw="CharisSIL-R.woff",
        direction="ltr",
    ),
)
WRITING_DEFAULTS[""] = dict(
    language="",
    fontName="Gentium",
    font="GentiumPlus-R.ttf",
    fontw="GentiumPlus-R.woff",
    direction="ltr",
)

FONT_BASE = (
    "https://github.com/annotation/text-fabric/blob/master/tf/server/static/fonts"
)

DEFAULT_CLS = "txtn"
DEFAULT_CLS_SRC = "txto"
DEFAULT_CLS_ORIG = "txtu"
DEFAULT_CLS_TRANS = "txtt"
DEFAULT_CLS_PHONO = "txtp"

FORMAT_CSS = dict(
    orig=DEFAULT_CLS_ORIG,
    trans=DEFAULT_CLS_TRANS,
    source=DEFAULT_CLS_SRC,
    phono=DEFAULT_CLS_PHONO,
)

LEVEL_DEFAULTS = dict(
    level={
        4: dict(flow="row"),
        3: dict(flow="row"),
        2: dict(flow="row"),
        1: dict(flow="row"),
        0: dict(flow="col"),
    },
    flow=dict(col=dict(wrap=False, stretch=False), row=dict(wrap=True, stretch=True)),
    wrap=None,
    stretch=None,
)

RELATIVE_DEFAULT = "tf"

MSPEC_KEYS = set(
    """
    org
    repo
    relative
    corpus
    docUrl
    doi
""".strip().split()
)

PROVENANCE_DEFAULTS = (
    ("org", None),
    ("repo", None),
    ("relative", RELATIVE_DEFAULT),
    ("graphicsRelative", None),
    ("version", None),
    ("moduleSpecs", ()),
    ("zip", None),
    ("corpus", "TF dataset (unspecified)"),
    ("doi", None),
    ("webBase", None),
    ("webHint", None),
    ("webLang", None),
    ("webLexId", None),
    ("webUrl", None),
    ("webUrlLex", None),
)

DOC_DEFAULTS = (
    ("docRoot", "{urlGh}"),
    ("docExt", ".md"),
    ("docBase", "{docRoot}/{org}/{repo}/blob/master/docs"),
    ("docPage", "home"),
    ("docUrl", "{docBase}/{docPage}{docExt}"),
    ("featureBase", None),
    ("featurePage", "home"),
    ("charUrl", "{tfDoc}/Writing/Transcription/{language}"),
    ("charText", "How TF features represent text"),
    ("webBase", None),
    ("webLang", None),
    ("webUrl", None),
    ("webUrlLex", None),
    ("webLexId", None),
    ("webHint", None),
)

DATA_DISPLAY_DEFAULTS = (
    ("excludedFeatures", set(), False),
    ("noneValues", {None}, False),
    ("sectionSep1", " ", False),
    ("sectionSep2", ":", False),
    ("textFormats", {}, False),
    ("browseNavLevel", None, True),
    ("browseContentPretty", False, False),
    ("exampleSection", None, True),
    ("exampleSectionHtml", None, True),
)

TYPE_KEYS = set(
    """
    base
    children
    childrenPlain
    chunkOf
    condense
    features
    featuresBare
    flow
    graphics
    hide
    label
    level
    lexOcc
    lineNumber
    stretch
    template
    transform
    verselike
    wrap
""".strip().split()
)

HOOKS = """
    afterChild
    childrenCustom
    plainCustom
    prettyCustom
""".strip().split()


class AppCurrent:
    def __init__(self, specs):
        self.update(specs)

    def update(self, specs):
        for (k, v) in specs.items():
            setattr(self, k, v)

    def get(self, k, v):
        return getattr(self, k, v)


class Check:
    def __init__(self, app, withApi):
        self.app = app
        self.withApi = withApi
        self.errors = []

    def checkSetting(self, k, v, extra=None):
        app = self.app
        withApi = self.withApi
        errors = self.errors
        dKey = self.dKey
        specs = app.specs

        if withApi:
            api = app.api
            F = api.F
            T = api.T
            Fall = api.Fall
            allNodeFeatures = set(Fall())
            nTypes = F.otype.all
            slotType = F.otype.slotType
            sectionTypes = T.sectionTypes

            if k in {"template", "label"}:
                (template, feats) = extra
                if template is not True and type(template) is not str:
                    errors.append(f"{k} must be `true` or a string")
                for feat in feats:
                    if feat not in allNodeFeatures:
                        if feat not in specs["transform"].get(dKey, {}):
                            errors.append(f"{k}: feature {feat} not loaded")
            elif k in {"featuresBare", "features"}:
                feats = extra[0]
                tps = extra[1].values()
                for feat in feats:
                    if feat not in allNodeFeatures:
                        errors.append(f"{k}: feature {feat} not loaded")
                for tp in tps:
                    if tp not in nTypes:
                        errors.append(f"{k}: node type {tp} not present")
            elif k == "base":
                if v and dKey == slotType:
                    errors.append(
                        f"{k}: No need to declare slot type {dKey} as base type"
                    )
            elif k == "lineNumber":
                if v not in allNodeFeatures:
                    errors.append(f"{k}: feature {v} not loaded")
            elif k == "textFormats":
                if type(v) is not dict:
                    errors.append(f"{k} must be a dictionary")
            elif k == "browseNavLevel":
                allowedValues = set(range(len(sectionTypes)))
                if v not in allowedValues:
                    allowed = ",".join(sorted(allowedValues))
                    errors.append(f"{k} must be an integer in {allowed}")
            elif k == "children":
                if type(v) is not str and type(v) is not list:
                    errors.append(f"{k} must be a (list of) node types")
                else:
                    v = {v} if type(v) is str else set(v)
                    for tp in v:
                        if tp not in nTypes:
                            errors.append(f"{k}: node type {tp} not present")
            elif k in {"lexOcc", "chunkOf"}:
                if type(v) is not str or v not in nTypes:
                    errors.append(f"{k}: node type {v} not present")
            elif k == "transform":
                for (feat, method) in extra.items():
                    if type(method) is str:
                        errors.append(
                            f"\t{k}:{feat}: {method}() not implemented in app"
                        )
            elif k in {
                "withTypes",
                "prettyTypes",
                "withNodes",
                "showFeatures",
                "lineNumbers",
                "showChunks",
                "showGraphics",
            }:
                allowed = self.extra[k]
                if not allowed and v is not None:
                    errors.append(
                        f"{k}={v} is not useful (dataset lacks relevant features)"
                    )
        else:
            if k in {"excludedFeatures", "noneValues"}:
                if type(v) is not list:
                    errors.append(f"{k} must be a list")
            elif k in {
                "sectionSep1",
                "sectionSep2",
                "exampleSection",
                "exampleSectionHtml",
            }:
                if type(v) is not str:
                    errors.append(f"{k} must be a string")
            elif k == "writing":
                allowedValues = set(WRITING_DEFAULTS)
                if v not in allowedValues:
                    allowed = ",".join(allowedValues - {""})
                    errors.append(f"{k} must be the empty string or one of {allowed}")
            elif k in {"direction", "language", "fontName", "font", "fontw"}:
                allowedValues = {w[k] for w in WRITING_DEFAULTS}
                if v not in allowedValues:
                    allowed = ",".join(allowedValues)
                    errors.append(f"{k} must be one of {allowed}")
            elif k in {
                "browseContentPretty",
                "base",
                "childrenPlain",
                "condense",
                "graphics",
                "hide",
                "stretch",
                "verselike",
                "wrap",
            }:
                allowedValues = {True, False}
                if v not in allowedValues:
                    allowed = "true,false"
                    errors.append(f"{k} must be a boolean in {allowed}")
            elif k == "flow":
                allowedValues = {"row", "col"}
                if v not in allowedValues:
                    allowed = ",".join(allowedValues)
                    errors.append(f"{k} must be a value in {allowed}")
            elif k == "level":
                allowedValues = set(range(len(4)))
                if v not in allowedValues:
                    allowed = ",".join(sorted(allowedValues))
                    errors.append(f"{k} must be an integer in {allowed}")

    def checkGroup(self, cfg, defaults, dKey, postpone=set(), extra=None):
        self.cfg = cfg
        self.defaults = defaults
        self.dKey = dKey
        self.extra = extra
        errors = []

        errors.clear()
        dSource = cfg.get(dKey, {})

        for (k, v) in dSource.items():
            if k in defaults:
                if k not in postpone:
                    self.checkSetting(k, v)
            else:
                errors.append(f"Illegal parameter `{k}` with value {v}")

    def checkItem(self, cfg, dKey):
        self.cfg = cfg
        self.dKey = dKey
        errors = self.errors

        errors.clear()
        if dKey in cfg:
            self.checkSetting(dKey, cfg[dKey])

    def report(self):
        errors = self.errors
        dKey = self.dKey

        if errors:
            console(f"App config error(s) in {dKey}:", error=True)
            for msg in errors:
                console(f"\t{msg}", error=True)

        self.errors = []


def setAppSpecs(app, cfg, reset=False):
    specs = dict(urlGh=URL_GH, urlNb=URL_NB, tfDoc=URL_TFDOC,)
    app.specs = specs
    specs.update(cfg)
    checker = Check(app, False)

    dKey = "writing"
    checker.checkItem(cfg, dKey)
    checker.report()
    value = cfg.get(dKey, "")
    specs[dKey] = value
    for (k, v) in WRITING_DEFAULTS[value].items():
        specs[k] = v
    extension = f" {value}" if value else ""
    defaultClsOrig = f"{DEFAULT_CLS_ORIG}{extension}"
    specs.update(extension=extension, defaultClsOrig=defaultClsOrig)

    for (dKey, defaults) in (
        ("provenanceSpec", PROVENANCE_DEFAULTS),
        ("docs", DOC_DEFAULTS),
    ):
        checker.checkGroup(cfg, {d[0] for d in defaults}, dKey)
        checker.report()
        dSource = cfg.get(dKey, {})
        for (k, v) in defaults:
            val = dSource.get(k, v)
            val = (
                None
                if val is None
                else val.format(**specs)
                if type(val) is str
                else val
            )
            specs[k] = val

    moduleSpecs = specs["moduleSpecs"] or []
    for moduleSpec in moduleSpecs:
        for k in MSPEC_KEYS:
            if k in moduleSpec:
                v = moduleSpec[k]
                if k == "docUrl" and v is not None:
                    v = v.format(**specs)
                    moduleSpec[k] = v
            else:
                moduleSpec[k] = (
                    specs.get(k, None)
                    if k in {"org", "repo"}
                    else RELATIVE_DEFAULT
                    if k == "relative"
                    else None
                )

    if specs["zip"] is None:
        org = specs["org"]
        repo = specs["repo"]
        graphicsRelative = specs["graphicsRelative"]
        graphicsModule = [(org, repo, graphicsRelative)] if graphicsRelative else []
        specs["zip"] = (
            [repo]
            + [(m["org"], m["repo"], m["relative"],) for m in moduleSpecs]
            + graphicsModule
        )

    for (dKey, method) in (
        ("dataDisplay", getDataDefaults),
        ("typeDisplay", getTypeDefaults),
    ):
        method(app, cfg, dKey, False)

    if reset:
        aContext = getattr(app, "context", None)
        if aContext:
            for key in HOOKS:
                specs[key] = aContext.get(key, {})
    else:
        for key in HOOKS:
            specs[key] = {}
    app.context = AppCurrent(specs)


def setAppSpecsApi(app, cfg):
    api = app.api
    T = api.T
    C = api.C
    sectionTypeSet = T.sectionTypeSet

    specs = app.specs

    specs["formatCls"] = compileFormatCls(app, specs["defaultClsOrig"])

    for (dKey, method) in (
        ("dataDisplay", getDataDefaults),
        ("typeDisplay", getTypeDefaults),
    ):
        method(app, cfg, dKey, True)

    specs["allowedBaseTypes"] = tuple(
        e[0] for e in C.levels.data if e[0] not in sectionTypeSet
    )

    specs["condenseTypes"] = C.levels.data
    specs["defaultFormat"] = T.defaultFormat

    dKey = "interfaceDefaults"
    interfaceDefaults = {inf[0]: inf[1] for inf in INTERFACE_OPTIONS}
    dSource = cfg.get(dKey, {})
    specific = {"lineNumbers", "showChunks", "showGraphics"}

    allowed = {}
    for (k, v) in interfaceDefaults.items():
        allow = (
            (
                k == "lineNumbers"
                and specs["lineNumberFeature"]
                or k == "showChunks"
                and specs["isChunkOf"]
                or k == "showGraphics"
                and specs["hasGraphics"]
            )
            if k in specific
            else True
        )
        if k in dSource:
            val = dSource[k]
            default = val if allow else None
        else:
            default = v if allow else None
        interfaceDefaults[k] = default
        allowed[k] = allow
    checker = Check(app, True)
    checker.checkGroup(cfg, interfaceDefaults, dKey, extra=allowed)
    checker.report()
    specs[dKey] = interfaceDefaults

    app.context.update(specs)
    app.showContext = types.MethodType(showContext, app)


def getDataDefaults(app, cfg, dKey, withApi):
    checker = Check(app, withApi)

    if withApi:
        api = app.api
        F = api.F
        T = api.T
        sectionTypes = T.sectionTypes

    specs = app.specs

    allowedKeys = {d[0] for d in DATA_DISPLAY_DEFAULTS}
    checker.checkGroup(cfg, allowedKeys, dKey)
    checker.report()

    givenInfo = cfg.get(dKey, {})

    for (attr, default, needsApi) in DATA_DISPLAY_DEFAULTS:
        if needsApi and not withApi or not needsApi and withApi:
            continue

        if attr == "browseNavLevel":
            default = len(sectionTypes) - 1 if sectionTypes else 1

        value = givenInfo.get(attr, specs.get(attr, default))
        if attr in specs and attr not in givenInfo:
            continue
        elif attr == "exampleSection":
            if not value:
                if sectionTypes:
                    verseType = sectionTypes[-1]
                    firstVerse = F.otype.s(verseType)[0]
                    value = app.sectionStrFromNode(firstVerse)
                else:
                    value = "passage"
            specs["exampleSection"] = value
            specs["exampleSectionHtml"] = f"<code>{value}</code>"
        else:
            specs[attr] = value


def getTypeDefaults(app, cfg, dKey, withApi):
    if not withApi:
        return

    checker = Check(app, withApi)
    givenInfo = cfg.get(dKey, {})

    api = app.api
    F = api.F
    T = api.T
    slotType = F.otype.slotType
    nTypes = F.otype.all
    structureTypes = T.structureTypes
    structureTypeSet = T.structureTypeSet
    sectionTypes = T.sectionTypes
    sectionTypeSet = T.sectionTypeSet

    sectionalTypeSet = sectionTypeSet | structureTypeSet

    specs = app.specs

    noChildren = set()
    isChunkOf = {}
    featuresBare = {}
    features = {}
    lineNumberFeature = {}
    hasGraphics = set()
    verseTypes = {sectionTypes[-1]} if sectionTypes else set()
    lexMap = {}
    allowedBaseTypes = {slotType}
    baseTypes = set()
    condenseType = None
    templates = {}
    labels = {}
    givenLevels = {}
    levels = {}
    childType = {}
    transform = {}

    specs["transform"] = transform

    for nType in nTypes:
        template = True if nType == slotType or nType in sectionalTypeSet else ""
        for dest in (templates, labels):
            dest[nType] = (template, ())

    unknownTypes = {nType for nType in givenInfo if nType not in nTypes}
    if unknownTypes:
        unknownTypesRep = ",".join(sorted(unknownTypes))
        console(f"App config error(s) in typeDisplay: {unknownTypesRep}", error=True)

    for (nType, info) in givenInfo.items():
        checker.checkGroup(
            givenInfo,
            TYPE_KEYS,
            nType,
            postpone={
                "base",
                "label",
                "template",
                "features",
                "featuresBare",
                "transform",
            },
        )
        checker.report()

        if info.get("verselike", False):
            verseTypes.add(nType)

        lOcc = info.get("lexOcc", None)
        if lOcc is not None:
            lexMap[lOcc] = nType

        if "base" in info:
            base = info.get("base", None)
            checker.checkSetting("base", base)
            baseTypes.add(nType)

        if "condense" in info:
            condenseType = nType

        trans = info.get("transform", None)
        if trans is not None:
            resolvedTrans = {}
            for (feat, func) in trans.items():
                methodName = f"transform_{func}"
                resolvedTrans[feat] = getattr(app, methodName, methodName)
            v = resolvedTrans
            checker.checkSetting("transform", trans, extra=v)
            transform[nType] = v

        for (k, dest) in (("template", templates), ("label", labels)):
            if k in info:
                template = info[k]
                templateFeatures = (
                    VAR_PATTERN.findall(template) if type(template) is str else ()
                )
                dest[nType] = (template, templateFeatures)
                checker.checkSetting(
                    k, template, extra=(template, templateFeatures),
                )

        for k in ("featuresBare", "features"):
            v = info.get(k, "")
            parsedV = parseFeatures(v)
            checker.checkSetting(k, v, extra=parsedV)
            if k == "features":
                features[nType] = parsedV
            else:
                featuresBare[nType] = parsedV

        lineNumber = info.get("lineNumber", None)
        if lineNumber is not None:
            lineNumberFeature[nType] = lineNumber

        graphics = info.get("graphics", False)
        if graphics:
            hasGraphics.add(nType)

        if not info.get("childrenPlain", True):
            noChildren.add(nType)

        chunkOf = info.get("chunkOf", None)
        if chunkOf is not None:
            isChunkOf[nType] = chunkOf

        verselike = info.get("verselike", False)
        if verselike:
            verseTypes.add(nType)

        if "level" in info or "flow" in info or "wrap" in info or "stretch" in info:
            givenLevels[nType] = {
                k: v for (k, v) in info.items() if k in LEVEL_DEFAULTS
            }

        if "children" in info:
            childs = info["children"] or ()
            if type(childs) is str:
                childs = {childs}
            else:
                childs = set(childs)
            childType[nType] = set(childs or ())

        checker.report()

    lexTypes = set(lexMap.values())

    levelTypes = [set(), set(), set(), set(), set()]
    levelTypes[4] = sectionalTypeSet - verseTypes
    levelTypes[3] = verseTypes
    levelTypes[0] = {slotType} | lexTypes

    remainingTypeSet = set(nTypes) - levelTypes[4] - levelTypes[3] - levelTypes[0]
    remainingTypes = tuple(x for x in nTypes if x in remainingTypeSet)
    nRemaining = len(remainingTypes)

    children = {
        nType: {nTypes[i + 1]}
        for (i, nType) in enumerate(nTypes)
        if nType in levelTypes[2] | levelTypes[1]
    }
    children.update(
        {
            nType: {nTypes[i + 1]}
            for (i, nType) in enumerate(structureTypes)
            if i < len(structureTypes) - 1
        }
    )
    children.update(
        {
            nType: {nTypes[i + 1]}
            for (i, nType) in enumerate(sectionTypes)
            if i < len(sectionTypes) - 1
        }
    )

    lowestSectionalTypes = set() | verseTypes
    if sectionTypes:
        lowestSectionalTypes.add(sectionTypes[-1])
    if structureTypes:
        lowestSectionalTypes.add(structureTypes[-1])

    biggestOtherType = remainingTypes[0] if remainingTypes else slotType
    smallestOtherType = remainingTypes[-1] if remainingTypes else None

    for lexType in lexTypes:
        if lexType in children:
            del children[lexType]

    for lowestSectionalType in lowestSectionalTypes:
        if lowestSectionalType not in children:
            children[lowestSectionalType] = {slotType}
        else:
            children[lowestSectionalType].add(slotType)

        if lowestSectionalType == biggestOtherType:
            continue
        children[lowestSectionalType].add(biggestOtherType)

    if smallestOtherType is not None and smallestOtherType != slotType:
        if smallestOtherType not in children:
            children[smallestOtherType] = {slotType}
        else:
            children[smallestOtherType].add(slotType)

    if nRemaining == 0:
        midType = slotType
    elif nRemaining == 1:
        midType = remainingTypes[0]
        levelTypes[1] = {midType}
    else:
        mid = len(remainingTypes) // 2
        midType = remainingTypes[mid]
        levelTypes[2] = set(remainingTypes[0:mid])
        levelTypes[1] = set(remainingTypes[mid:])

    if condenseType is None:
        condenseType = sectionTypes[-1] if sectionTypes else midType

    for (i, nTypes) in enumerate(levelTypes):
        for nType in nTypes:
            levels[nType] = getLevel(i, givenLevels.get(nType, {}), nType in verseTypes)

    for (nType, childInfo) in children.items():
        if nType not in childType:
            childType[nType] = childInfo

    levelCls = {}

    for (nType, nTypeInfo) in levels.items():
        level = nTypeInfo["level"]
        flow = nTypeInfo["flow"]
        wrap = nTypeInfo["wrap"]

        containerCls = f"contnr c{level}"
        labelCls = f"lbl c{level}"
        childrenCls = (
            f"children {flow} {'wrap' if wrap else ''}"
            if childType.get(nType, None)
            else ""
        )

        levelCls[nType] = dict(
            container=containerCls, label=labelCls, children=childrenCls,
        )

    if not baseTypes:
        baseTypes = None

    specs.update(
        allowedBaseTypes=allowedBaseTypes,
        baseTypes=baseTypes,
        childType=childType,
        chunkedTypes=set(isChunkOf.values()),
        condenseType=condenseType,
        features=features,
        featuresBare=featuresBare,
        hasGraphics=hasGraphics,
        isChunkOf=isChunkOf,
        labels=labels,
        levels=levels,
        levelCls=levelCls,
        lexMap=lexMap,
        lexTypes=lexTypes,
        lineNumberFeature=lineNumberFeature,
        noChildren=noChildren,
        noDescendTypes=lexTypes,
        templates=templates,
        transform=transform,
        verseTypes=verseTypes,
    )


def showContext(app):
    EM = "*empty*"
    block = "    "

    def eScalar(x, plain=True):
        tick = "`" if plain else ""
        return f"{tick}{mdEsc(str(x))}{tick}" if x else EM

    def eEmpty(x):
        tpv = type(x)
        return (
            "`[]`"
            if tpv is list
            else "`()`"
            if tpv is tuple
            else "`{}`"
            if tpv is dict
            else "`set()`"
            if tpv is set
            else EM
            if tpv is str
            else str(x)
        )

    def eList(x, level):
        tpv = type(x)
        indent = block * level
        md = "\n"
        for (i, v) in enumerate(sorted(x, key=lambda y: str(y)) if tpv is set else x):
            item = f"{i + 1}." if level == 0 else "*"
            md += f"{indent}{item:<4}{eData(v, level + 1)}"
        return md

    def eDict(x, level):
        indent = block * level
        md = "\n"
        for (i, (k, v)) in enumerate(sorted(x.items(), key=lambda y: str(y))):
            item = f"{i + 1:}." if level == 0 else "*"
            md += (
                f"{indent}{item:<4}**{eScalar(k, plain=level > 0)}**:"
                f" {eData(v, level + 1)}"
            )
        return md

    def eRest(x, level):
        indent = block * level
        return "\n" + indent + eScalar(x) + "\n"

    def eData(x, level):
        if not x:
            return eEmpty(x) + "\n"
        tpv = type(x)
        if tpv is str or tpv is float or tpv is int or tpv is bool:
            return eScalar(x) + "\n"
        if tpv is list or tpv is tuple or tpv is set:
            return eList(x, level)
        if tpv is dict:
            return eDict(x, level)
        return eRest(x, level)

    dm(
        f"""\
# {(app.appName)} settings

{eData(app.specs, 0)}
"""
    )


def getLevel(defaultLevel, givenInfo, isVerse):
    level = givenInfo.get("level", defaultLevel)
    defaultsFromLevel = LEVEL_DEFAULTS["level"][level]
    flow = givenInfo.get("flow", "row" if isVerse else defaultsFromLevel["flow"])
    defaultsFromFlow = LEVEL_DEFAULTS["flow"][flow]
    wrap = givenInfo.get("wrap", defaultsFromFlow["wrap"])
    stretch = givenInfo.get("stretch", defaultsFromFlow["stretch"])
    return dict(level=level, flow=flow, wrap=wrap, stretch=stretch)


def compileFormatCls(app, defaultClsOrig):
    api = app.api
    T = api.T

    result = {None: defaultClsOrig}
    for fmt in T.formats:
        for (key, cls) in FORMAT_CSS.items():
            if (
                f"-{key}-" in fmt
                or fmt.startswith(f"{key}-")
                or fmt.endswith(f"-{key}")
            ):
                result[fmt] = cls
    for fmt in T.formats:
        if fmt not in result:
            result[fmt] = DEFAULT_CLS
    return result


def parseFeatures(features):
    bare = []
    indirect = {}
    for feat in features.split(" "):
        if not feat:
            continue
        parts = feat.split(":", 1)
        feat = parts[-1]
        bare.append(feat)
        if len(parts) > 1:
            indirect[feat] = parts[0]
    return (bare, indirect)
