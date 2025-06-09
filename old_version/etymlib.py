from __future__ import annotations
from typing import TypeAlias
from networkx import DiGraph
from json import load


def split_root(root: RootLike):
    '''splits RootLike into 3 strings'''
    if isinstance(root, Root):
        return str(root).split()
    elif isinstance(root, str):
        return root.split()


class EtymologyData():
    '''database of etymologies and language families'''

    def __init__(self, path: str | None = None):
        if not path:
            self.roots, self.langs = (DiGraph(), DiGraph())

    def __getitem__(self, value: LangLike | RootLike) -> Lang | Root:
        if not isinstance(value, str):
            value = str(value)
        if len(value.split()) == 3:
            return next(n for n in self.roots.nodes if n == value)
        elif len(value.split()) == 1:
            return next(n for n in self.langs.nodes if n == value)

    def add_root(self, root: str, *sources: str) -> Root:
        if not sources:
            return Root(root, self)
        elif sources:
            sources = [self.add_root(source) for source in sources]
            root = self.add_root(root)
            for source in sources:
                self.roots.add_edge(source, root)
            return root

    def add_langs(self, *langs: str, source: str = None):
        if not source:
            for lang in langs:
                if lang not in self.langs:
                    self.langs.add_node(Lang(lang, self))
        if source:
            self.add_langs(source)
            for lang in langs:
                if lang not in self.langs:
                    self.langs.add_node(Lang(lang, self))
                    self.langs.add_edge(self[source], self[lang])

    def read_langs_json(self, path: str):
        with open(path) as f:
            data = load(f)
        for line in data:
            self.add_langs(*line['langs'], source=line['source'])

    def read_roots_json(self, path: str):
        with open(path) as f:
            lang = f.name.split('.')[0].split('/')[-1]
            data = load(f)
        for root in data:
            if not root['source']:
                root['source'] = []
        for root in sorted(data, key=lambda x: len(x['source'])):
            self.add_root(' '.join([lang, root['root']]), *root['source'])


class Root():
    '''a class for a word or affix'''

    def __init__(self, root: RootLike, db: EtymologyData):
        self.lang, self.text, self.gloss = split_root(root)
        self.db = db
        db.roots.add_node(self)

    def __repr__(self) -> str:
        return ' '.join((self.lang, self.text, self.gloss))

    def __str__(self):
        return ' '.join((self.lang, self.text, self.gloss))

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, value) -> bool:
        return str(self) == value

    def replace(self, root: RootLike = None, text: str = None,
                gloss: str = None, lang: LangLike = None) -> Root:
        '''replaces root data'''
        if root:
            self.text, self.gloss, self.lang = split_root(root)
        if gloss:
            self.gloss = gloss
        if text:
            self.text = text
        if lang:
            self.lang = lang
        return self

    def sources(self):
        return [source for source in self.db.roots.predecessors(self)]

    def txt_line(self) -> str:
        if self.sources():
            return ' '.join((self.text, self.gloss, 'from', *self.sources()))
        else:
            return ' '.join((self.text, self.gloss))

    def json_line(self) -> dict:
        if self.sources():
            return {'root': ' '.join((self.text, self.gloss)), 'source':
                    [str(source) for source in self.sources]}


class Wordlist(list):
    '''a class for groups of roots'''

    def __init__(self, roots: RootListLike, db: EtymologyData,
                 lang: Lang = None):
        if isinstance(roots, RootLike):
            roots = [roots]
        super().__init__(roots)
        self.lang = lang

    def __repr__(self) -> str:
        if not self.lang:
            return super().__repr__()
        else:
            return self.lang + super().__repr__()

    def descend(self, roots: RootListLike) -> Wordlist:
        '''descends each word'''
        if len(self) == len(roots):
            return [u.descend(v) for u, v in zip(self, roots)]
        else:
            raise ValueError('lists are of different lengths')


class Lang():
    '''a class for a language'''

    def __init__(self, name: str, db: EtymologyData,):
        self.name = name
        self.db = db
        db.langs.add_node(self)

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> str:
        return self.name.__hash__()

    def __eq__(self, value) -> bool:
        return self.name == value

    def __getitem__(self, value) -> Root:
        pass

    def descend(self, *names: LangLike) -> Lang:
        '''creates a child language'''
        for n in names:
            if n not in self.db.langs:
                Lang(n, self.db)

    def ascend(self, name: str) -> Lang:
        '''creates a parent language if one is not present'''
        if name not in self.db.langs and not self.db.langs.predecessors():
            self.db.langs.add_edge(Lang(name, self.db), self)
            return Lang(name, self.db)

    def rename(self, name: str) -> Lang:
        '''renames a language, modifies its words to match'''
        self.name = name

    def wordlist(self, glosses: list[str] = None) -> Wordlist:
        '''returns a wordlist of specified glosses'''
        pass

    def txt_line(self) -> str:
        '''turns lang and source info to a line of readable text'''
        pass

    def json_line(self) -> dict:
        '''turns lang and source info to a dict for a json file'''
        pass


RootLike: TypeAlias = Root | str
LangLike: TypeAlias = Lang | str
RootListLike: TypeAlias = RootLike | list[RootLike]
