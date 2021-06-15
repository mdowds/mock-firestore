import warnings
from itertools import islice, tee
from typing import Iterator, Any, Optional, List, Callable, Union

from mockfirestore.document import DocumentSnapshot
from mockfirestore._helpers import T


class Query:
    def __init__(self, parent: 'CollectionReference', projection=None,
                 field_filters=(), orders=(), limit=None, offset=None,
                 start_at=None, end_at=None, all_descendants=False) -> None:
        self.parent = parent
        self.projection = projection
        self._field_filters = []
        self.orders = list(orders)
        self._limit = limit
        self._offset = offset
        self._start_at = start_at
        self._end_at = end_at
        self.all_descendants = all_descendants

        if field_filters:
            for field_filter in field_filters:
                self._add_field_filter(*field_filter)

    def stream(self, transaction=None) -> Iterator[DocumentSnapshot]:
        doc_snapshots = self.parent.stream()

        for field, compare, value in self._field_filters:
            doc_snapshots = [doc_snapshot for doc_snapshot in doc_snapshots
                             if compare(doc_snapshot._get_by_field_path(field), value)]

        if self.orders:
            for key, direction in self.orders:
                doc_snapshots = sorted(doc_snapshots,
                                       key=lambda doc: doc.to_dict()[key],
                                       reverse=direction == 'DESCENDING')
        if self._start_at:
            document_fields_or_snapshot, before = self._start_at
            doc_snapshots = self._apply_cursor(document_fields_or_snapshot, doc_snapshots, before, True)

        if self._end_at:
            document_fields_or_snapshot, before = self._end_at
            doc_snapshots = self._apply_cursor(document_fields_or_snapshot, doc_snapshots, before, False)

        if self._offset:
            doc_snapshots = islice(doc_snapshots, self._offset, None)

        if self._limit:
            doc_snapshots = islice(doc_snapshots, self._limit)

        return iter(doc_snapshots)

    def get(self) -> Iterator[DocumentSnapshot]:
        warnings.warn('Query.get is deprecated, please use Query.stream',
                      category=DeprecationWarning)
        return self.stream()

    def _add_field_filter(self, field: str, op: str, value: Any):
        compare = self._compare_func(op)
        self._field_filters.append((field, compare, value))

    def where(self, field: str, op: str, value: Any) -> 'Query':
        self._add_field_filter(field, op, value)
        return self

    def order_by(self, key: str, direction: Optional[str] = 'ASCENDING') -> 'Query':
        self.orders.append((key, direction))
        return self

    def limit(self, limit_amount: int) -> 'Query':
        self._limit = limit_amount
        return self

    def offset(self, offset_amount: int) -> 'Query':
        self._offset = offset_amount
        return self

    def start_at(self, document_fields_or_snapshot: Union[dict, DocumentSnapshot]) -> 'Query':
        self._start_at = (document_fields_or_snapshot, True)
        return self

    def start_after(self, document_fields_or_snapshot: Union[dict, DocumentSnapshot]) -> 'Query':
        self._start_at = (document_fields_or_snapshot, False)
        return self

    def end_at(self, document_fields_or_snapshot: Union[dict, DocumentSnapshot]) -> 'Query':
        self._end_at = (document_fields_or_snapshot, True)
        return self

    def end_before(self, document_fields_or_snapshot: Union[dict, DocumentSnapshot]) -> 'Query':
        self._end_at = (document_fields_or_snapshot, False)
        return self

    def _apply_cursor(self, document_fields_or_snapshot: Union[dict, DocumentSnapshot], doc_snapshot: Iterator[DocumentSnapshot],
                      before: bool, start: bool) -> Iterator[DocumentSnapshot]:
        docs, doc_snapshot = tee(doc_snapshot)
        for idx, doc in enumerate(doc_snapshot):
            index = None
            if isinstance(document_fields_or_snapshot, dict):
                for k, v in document_fields_or_snapshot.items():
                    if doc.to_dict().get(k, None) == v:
                        index = idx
                    else:
                        index = None
                        break
            elif isinstance(document_fields_or_snapshot, DocumentSnapshot):
                if doc.id == document_fields_or_snapshot.id:
                    index = idx
            if index is not None:
                if before and start:
                    return islice(docs, index, None, None)
                elif not before and start:
                    return islice(docs, index + 1, None, None)
                elif before and not start:
                    return islice(docs, 0, index + 1, None)
                elif not before and not start:
                    return islice(docs, 0, index, None)

    def _compare_func(self, op: str) -> Callable[[T, T], bool]:
        if op == '==':
            return lambda x, y: x == y
        elif op == '!=':
            return lambda x, y: x != y
        elif op == '<':
            return lambda x, y: x < y
        elif op == '<=':
            return lambda x, y: x <= y
        elif op == '>':
            return lambda x, y: x > y
        elif op == '>=':
            return lambda x, y: x >= y
        elif op == 'in':
            return lambda x, y: x in y
        elif op == 'array_contains':
            return lambda x, y: y in x
        elif op == 'array_contains_any':
            return lambda x, y: any([val in y for val in x])
