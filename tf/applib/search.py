"""
Calls from the advanced API to the Search API.
"""

import types

from ..core.helpers import console
from .condense import condense


def searchApi(app):
    app.search = types.MethodType(search, app)


def search(app, query, silent=False, sets=None, shallow=False, sort=True):
    """Search with some high-level features.

    This function calls the lower level `tf.search.search.Search` facility aka `S`.
    But whereas the `S` version returns a generator which yields the results
    one by one, the `A` version collects all results and sorts them in the
    [canonical order](../Api/Nodes.md#navigating-nodes).
    (but you can change the sorting, see the `sort` parameter).
    It then reports the number of results.

    It will also set the display parameter `tupleFeatures` (see below)
    in such a way that subsequent calls to `tf.applib.display.export` emit
    the features that have been used in the query.

    query: dict
        the [search template](../Use/Search.md#search-template-reference)
        that has to be searched for.

    silent: boolean, optional `False`
        if `True` it will suppress the reporting of the number of results.

    shallow: boolean, optional `False`
        If `True` or `1`, the result is a set of things that match the top-level element
        of the `query`.

        If `2` or a bigger number *n*, return the set of truncated result tuples: only
        the first *n* members of each tuple are retained.

        If `False` or `0`, a list of all result tuples will be returned.

    sets: dict, optional `None`
        If not `None`, it should be a dictionary of sets, keyed by a names.
        In `query` you can refer to those names to invoke those sets.

        For example, if you have a set `gappedPhrases` of all phrase nodes
        that have a gap, you can pass `sets=dict(gphrase=gappedPhrases)`,
        and then in your query you can say

        ```
        gphrase function=Pred
          word sp=verb
        ```

        etc.

        This is handy when you need node sets that cannot be conveniently queried.
        You can produce them by hand-coding.
        Once you got them, you can use them over and over again in queries.
        Or you can save them with [writeSets](Lib.md#sets)
        and use them in the TF browser.

    sort: boolean, optional `True`
        If `True` (default), search results will be returned in
        [canonical order](../Api/Nodes.md#navigating-nodes).

        !!! note "canonical sort key for tuples"
            This sort is achieved by using the function
            [sortKeyTuple](../Api/Nodes.md#navigating-nodes)
            as sort key.

        If it is a *sort key*, i.e. function that can be applied to tuples of nodes
        returning values, then this key will be used to sort the results.

        If it is a `False` value, no sorting will be applied.

    !!! hint "search template reference"
        See the [search template reference](../Use/Search.md#search-templates)
    """

    api = app.api
    info = api.info
    isSilent = api.isSilent
    setSilent = api.setSilent
    S = api.S
    sortKeyTuple = api.sortKeyTuple

    wasSilent = isSilent()

    results = S.search(query, sets=sets, shallow=shallow)
    if not shallow:
        if not sort:
            results = list(results)
        elif sort is True:
            results = sorted(results, key=sortKeyTuple)
        else:
            try:
                sortedResults = sorted(results, key=sort)
            except Exception as e:
                console(
                    (
                        "WARNING: your sort key function caused an error\n"
                        f"{str(e)}"
                        "\nYou get unsorted results"
                    ),
                    error=True,
                )
                sortedResults = list(results)
            results = sortedResults

        features = ()
        if S.exe:
            qnodes = getattr(S.exe, "qnodes", [])
            nodeMap = getattr(S.exe, "nodeMap", {})
            features = tuple(
                (i, tuple(sorted(set(q[1].keys()) | nodeMap.get(i, set()))))
                for (i, q) in enumerate(qnodes)
            )
            app.displaySetup(tupleFeatures=features)

    nResults = len(results)
    plural = "" if nResults == 1 else "s"
    setSilent(silent)
    info(f"{nResults} result{plural}")
    setSilent(wasSilent)
    return results


def runSearch(app, query, cache):
    api = app.api
    S = api.S
    plainSearch = S.search

    cacheKey = (query, False)
    if cacheKey in cache:
        return cache[cacheKey]
    options = dict(msgCache=[])
    if app.sets is not None:
        options["sets"] = app.sets
    (queryResults, messages, exe) = plainSearch(query, here=False, **options)
    features = ()
    if exe:
        qnodes = getattr(exe, "qnodes", [])
        nodeMap = getattr(S.exe, "nodeMap", {})
        features = tuple(
            (i, tuple(sorted(set(q[1].keys()) | nodeMap.get(i, set()))))
            for (i, q) in enumerate(qnodes)
        )
    queryResults = tuple(sorted(queryResults))
    cache[cacheKey] = (queryResults, messages, features)
    return (queryResults, messages, features)


def runSearchCondensed(app, query, cache, condenseType):
    api = app.api
    cacheKey = (query, True, condenseType)
    if cacheKey in cache:
        return cache[cacheKey]
    (queryResults, messages, features) = runSearch(app, query, cache)
    queryResults = condense(api, queryResults, condenseType, multiple=True)
    cache[cacheKey] = (queryResults, messages, features)
    return (queryResults, messages, features)
