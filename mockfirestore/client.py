from typing import Iterable
from mockfirestore.collection import CollectionReference
from mockfirestore.document import DocumentReference, DocumentSnapshot
from mockfirestore.transaction import Transaction


class MockFirestore:

    def __init__(self) -> None:
        self._data = {}

    def _ensure_path(self, path):
        current_position = self

        for el in path[:-1]:
            if type(current_position) in (MockFirestore, DocumentReference):
                current_position = current_position.collection(el)
            else:
                current_position = current_position.document(el)

        return current_position

    def document(self, path: str) -> DocumentReference:
        path = path.split("/")

        if len(path) % 2 != 0:
            raise Exception("Cannot create document at path {}".format(path))
        current_position = self._ensure_path(path)

        return current_position.document(path[-1])

    def collection(self, path: str) -> CollectionReference:
        path = path.split("/")

        if len(path) % 2 != 1:
            raise Exception("Cannot create collection at path {}".format(path))

        name = path[-1]
        if len(path) > 1:
            current_position = self._ensure_path(path)
            return current_position.collection(name)
        else:
            if name not in self._data:
                self._data[name] = {}
            return CollectionReference(self._data, [name])

    def collections(self) -> Iterable[CollectionReference]:
        for collection_name in self._data:
            yield CollectionReference(self._data, [collection_name])

    def reset(self):
        self._data = {}

    def get_all(self, references: Iterable[DocumentReference],
                field_paths=None,
                transaction=None) -> Iterable[DocumentSnapshot]:
        for doc_ref in set(references):
            yield doc_ref.get()

    def transaction(self, **kwargs) -> Transaction:
        return Transaction(self, **kwargs)


