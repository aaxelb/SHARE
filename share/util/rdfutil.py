import typing

import gather


class IriLabeler:
    def __init__(
        self,
        vocabulary: gather.RdfTripleDictionary,
        language_iris: typing.Iterable[str] = (),
        label_iri: str = gather.RDFS.label,
    ):
        self.vocabulary = vocabulary
        self.language_iris = frozenset(language_iris)
        self.label_iri = label_iri

    def all_iris_by_label(self) -> dict[str, str]:
        try:
            return self.__iris_by_label
        except AttributeError:
            _iris_by_label = {}
            for _iri in self.vocabulary:
                try:
                    _iris_by_label[self._find_label(_iri)] = _iri
                except ValueError:
                    pass  # no label, is ok
            self.__iris_by_label = _iris_by_label
            return _iris_by_label

    def all_labels_by_iri(self) -> dict[str, str]:
        try:
            return self.__labels_by_iri
        except AttributeError:
            _iris_by_label = self.all_iris_by_label()
            _labels_by_iri = {
                _iri: _label
                for _label, _iri in _iris_by_label.items()
            }
            _missing_iris = (
                set(_iris_by_label.values())
                .difference(_labels_by_iri.keys())
            )
            if _missing_iris:
                raise ValueError(f'vocab label collision! missing labels for {_missing_iris}')
            self.__labels_by_iri = _labels_by_iri
            return _labels_by_iri

    def iri_for_label(self, label: str) -> str:
        return self.all_iris_by_label()[label]  # may raise KeyError

    def label_for_iri(self, iri: str) -> str:
        return self.all_labels_by_iri()[iri]  # may raise KeyError

    def get_label_or_iri(self, iri: str) -> str:
        try:
            return self.label_for_iri(iri)
        except KeyError:
            return iri

    def _find_label(self, iri: str) -> str:
        _labelset = (
            self.vocabulary
            .get(iri, {})
            .get(self.label_iri, ())
        )
        try:
            return next(
                _label.unicode_text
                for _label in _labelset
                if (
                    isinstance(_label, gather.Text)
                    and self.language_iris.issubset(_label.language_iris)
                )
            )
        except StopIteration:
            raise ValueError(f'could not find label for iri "{iri}"')
