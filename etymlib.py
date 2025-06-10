from __future__ import annotations
from networkx import DiGraph
from networkx import node_link_data as nl_data, node_link_graph as nl_graph
from json import load, dump


class EtymologyData():
    '''the whole database'''

    def __init__(self, path: str | None = None):
        self.lang_graph, self.root_graph = DiGraph(), DiGraph()
        self.langs, self.roots = {}, {}
        if path:
            self.read_json(path)

    def _dict_json(self) -> dict:
        '''returns database as a dict, relying on sources for relationships'''
        return {'root_graph': None, 'lang_graph': None,
                'langs': [v._dict_json() for k, v in self.langs.items()],
                'roots': [v._dict_json() for k, v in self.roots.items()]}

    def _graph_json(self) -> dict:
        '''returns database as a dict, relying on graphs for relationships'''
        return {'lang_graph': nl_data(self.lang_graph, edges='edges'),
                'root_graph': nl_data(self.root_graph, edges='edges'),
                'langs': [v._graph_json() for k, v in self.langs.items()],
                'roots': [v._graph_json() for k, v in self.roots.items()]}

    def _create_lang(self, name: str, info: dict | None = None):
        '''adds a lang to the graph and database'''
        if name not in self.langs:
            self.lang_graph.add_node(name)
            self.langs[name] = Lang(name, self, info)
        elif info:
            self.langs[name].info = info

    def _create_root(self, root: str, info: dict | None = None):
        '''adds a root to the graph and database'''
        if root not in self.roots:
            self.root_graph.add_node(root)
            self.roots[root] = Root(root, self, info)
        elif info:
            self.roots[root].info = info

    def add_lang(self, name: str, source: str | None = None,
                 info: dict | None = None) -> Lang:
        '''adds a lang to the graph and database with a source'''
        if not source:
            self._create_lang(name, info)
        elif source:
            self._create_lang(source)
            self._create_lang(name, info)
            self.lang_graph.add_edge(source, name)
        return self.langs[name]

    def add_root(self, root: str, sources: list[str] | None = None,
                 info: dict | None = None) -> Root:
        '''adds a root to the graph and database with a source'''
        if not sources:
            self._create_root(root, info)
        elif sources:
            self._create_root(root, info)
            for source in sources:
                self._create_root(source)
                self.root_graph.add_edge(source, root)
        return self.roots[root]

    def add_langs(self, names: list[str], source: str | None = None,
                  info: dict | None = None):
        '''adds a list of langs to the graph and database with a source'''
        if not source:
            for name in names:
                self._create_lang(name, info)
        elif source:
            self._create_lang(source)
            for name in names:
                self._create_lang(name)
                self.lang_graph.add_edge(source, name)

    def add_roots(self, roots: list[str], sources: list[str] | None = None,
                  info: dict | None = None):
        '''adds a list of roots to the graph and database with a source'''
        if not sources:
            for root in roots:
                self._create_root(root, info)
        elif sources:
            for source in sources:
                self._create_root(source)
            for root in roots:
                self._create_root(root, info)
                for source in sources:
                    self.root_graph.add_edge(source, root)

    def add_langs_from(self, langs: list[str],
                       sources: list[str | None] | None = None,
                       info: dict | None = None):
        '''adds a list of langs with an optional list of sources'''
        for lang, source in zip(langs, sources):
            self.add_lang(lang, source, info)

    def add_roots_from(self, roots: list[str],
                       sources: list[list[str | None]] | None = None,
                       info: dict | None = None):
        '''adds a list of roots with an optional list of sources'''
        if sources:
            for root, sources in zip(roots, sources):
                self.add_root(root, sources, info)
        else:
            for root in roots:
                self.add_root(root, info)

    def write_graph_json(self, path: str):
        '''writes data to a json file as 2 graphs and 2 lists'''
        with open(path, 'w') as f:
            dump(self._graph_json(), f, indent=4)

    def write_dict_json(self, path: str):
        '''writes data to a json file as 2 lists'''
        with open(path, 'w') as f:
            dump(self._dict_json(), f, indent=4)

    def read_json(self, path: str):
        '''reads in a json file'''
        with open(path) as f:
            data = load(f)
        if data['lang_graph'] or data['root_graph']:
            self.langs_graph = nl_graph(data['lang_graph'], edges='edges')
            self.roots_graph = nl_graph(data['root_graph'], edges='edges')
            for lang in data['langs']:
                self._create_lang(lang['name'], lang['info'])
            for root in data['roots']:
                self._create_root(root['root'], root['info'])
        else:
            for lang in data['langs']:
                self.add_lang(lang['name'], lang['source'], lang['info'])
            for root in data['roots']:
                self.add_root(root['root'], root['sources'], root['info'])


class Lang():
    '''a language'''

    def __init__(self, name: str, db: EtymologyData,
                 info: dict | None = None):
        self.name, self.db, self.info = name, db, info

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    def __getitem__(self, key: str) -> Root:
        if key[0] == '<':
            return next(self.db.roots[root] for root in self.vocab()
                        if root.split()[2] == key.strip('<').strip('>'))
        else:
            return next(self.db.roots[root] for root in self.vocab()
                        if root.split()[1] == key)

    def _graph_json(self) -> dict:
        '''returns serializable lang data'''
        return {'name': self.name,
                'info': self.info}

    def _dict_json(self) -> dict:
        '''returns serializable lang data with sources'''
        return {'name': self.name,
                'source': self.source(),
                'info': self.info}

    def source(self) -> str | None:
        '''returns source language'''
        if any(self.db.lang_graph.predecessors(str(self))):
            return next(self.db.lang_graph.predecessors(str(self)))
        else:
            return None

    def children(self) -> list[str]:
        '''returns child languages'''
        return list(self.db.lang_graph.successors(str(self)))

    def vocab(self) -> list[str]:
        '''returns a list of strings of all roots in the language'''
        return [root for root in self.db.root_graph
                if root.split()[0] == str(self)]


class Root():
    '''a word or affix at one point in time'''

    def __init__(self, root: str, db: EtymologyData,
                 info: dict | None = None):
        self.lang, self.text, self.gloss = root.split()
        self.db, self.info = db, info

    def __repr__(self) -> str:
        return ' '.join([self.lang,
                         self.text.join(["'", "'"]),
                         self.gloss.join(['<', '>'])])

    def __str__(self) -> str:
        return ' '.join([self.lang, self.text, self.gloss])

    def _graph_json(self) -> dict:
        '''returns serializable root data'''
        return {'root': str(self),
                'info': self.info}

    def _dict_json(self) -> dict:
        return {'root': str(self),
                'sources': self.sources(),
                'info': self.info}

    def language(self) -> Lang:
        return self.db.langs[self.lang]

    def sources(self) -> list[str]:
        '''returns list of source roots'''
        return list(self.db.root_graph.predecessors(str(self)))

    def children(self) -> list[str]:
        '''returns list of child roots'''
        return list(self.db.root_graph.predecessors(str(self)))

    def is_compound(self) -> bool:
        '''true if the root has more than one source'''
        return len(self.sources()) > 1

    def is_inherited(self) -> bool:
        '''true if the source language is the parent language'''
        if self.is_compound():
            return False
        elif self.sources():
            return self.sources()[0].split()[0] == self.language().source()
