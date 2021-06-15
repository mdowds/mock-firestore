from unittest import TestCase

from mockfirestore import MockFirestore, DocumentReference, DocumentSnapshot, AlreadyExists


class TestCollectionReference(TestCase):
    def test_collection_get_returnsDocuments(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2}
        }}
        docs = list(fs.collection('foo').stream())

        self.assertEqual({'id': 1}, docs[0].to_dict())
        self.assertEqual({'id': 2}, docs[1].to_dict())

    def test_collection_get_collectionDoesNotExist(self):
        fs = MockFirestore()
        docs = fs.collection('foo').stream()
        self.assertEqual([], list(docs))

    def test_collection_get_nestedCollection(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {
                'id': 1,
                'bar': {
                    'first_nested': {'id': 1.1}
                }
            }
        }}
        docs = list(fs.collection('foo').document('first').collection('bar').stream())
        self.assertEqual({'id': 1.1}, docs[0].to_dict())

    def test_collection_get_nestedCollection_by_path(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {
                'id': 1,
                'bar': {
                    'first_nested': {'id': 1.1}
                }
            }
        }}
        docs = list(fs.collection('foo/first/bar').stream())
        self.assertEqual({'id': 1.1}, docs[0].to_dict())

    def test_collection_get_nestedCollection_collectionDoesNotExist(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        docs = list(fs.collection('foo').document('first').collection('bar').stream())
        self.assertEqual([], docs)

    def test_collection_get_nestedCollection_by_path_collectionDoesNotExist(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        docs = list(fs.collection('foo/first/bar').stream())
        self.assertEqual([], docs)

    def test_collection_get_ordersByAscendingDocumentId_byDefault(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'beta': {'id': 1},
            'alpha': {'id': 2}
        }}
        docs = list(fs.collection('foo').stream())
        self.assertEqual({'id': 2}, docs[0].to_dict())

    def test_collection_whereEquals(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'valid': True},
            'second': {'gumby': False}
        }}

        docs = list(fs.collection('foo').where('valid', '==', True).stream())
        self.assertEqual({'valid': True}, docs[0].to_dict())

    def test_collection_whereNotEquals(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1},
            'second': {'count': 5}
        }}

        docs = list(fs.collection('foo').where('count', '!=', 1).stream())
        self.assertEqual({'count': 5}, docs[0].to_dict())

    def test_collection_whereLessThan(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1},
            'second': {'count': 5}
        }}

        docs = list(fs.collection('foo').where('count', '<', 5).stream())
        self.assertEqual({'count': 1}, docs[0].to_dict())

    def test_collection_whereLessThanOrEqual(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1},
            'second': {'count': 5}
        }}

        docs = list(fs.collection('foo').where('count', '<=', 5).stream())
        self.assertEqual({'count': 1}, docs[0].to_dict())
        self.assertEqual({'count': 5}, docs[1].to_dict())

    def test_collection_whereGreaterThan(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1},
            'second': {'count': 5}
        }}

        docs = list(fs.collection('foo').where('count', '>', 1).stream())
        self.assertEqual({'count': 5}, docs[0].to_dict())

    def test_collection_whereGreaterThanOrEqual(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1},
            'second': {'count': 5}
        }}

        docs = list(fs.collection('foo').where('count', '>=', 1).stream())
        self.assertEqual({'count': 1}, docs[0].to_dict())
        self.assertEqual({'count': 5}, docs[1].to_dict())

    def test_collection_whereMissingField(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1},
            'second': {'count': 5}
        }}

        docs = list(fs.collection('foo').where('no_field', '==', 1).stream())
        self.assertEqual(len(docs), 0)

    def test_collection_whereNestedField(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'nested': {'a': 1}},
            'second': {'nested': {'a': 2}}
        }}

        docs = list(fs.collection('foo').where('nested.a', '==', 1).stream())
        self.assertEqual(len(docs), 1)
        self.assertEqual({'nested': {'a': 1}}, docs[0].to_dict())

    def test_collection_whereIn(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'field': 'a1'},
            'second': {'field': 'a2'},
            'third': {'field': 'a3'},
            'fourth': {'field': 'a4'},
        }}

        docs = list(fs.collection('foo').where('field', 'in', ['a1', 'a3']).stream())
        self.assertEqual(len(docs), 2)
        self.assertEqual({'field': 'a1'}, docs[0].to_dict())
        self.assertEqual({'field': 'a3'}, docs[1].to_dict())

    def test_collection_whereArrayContains(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'field': ['val4']},
            'second': {'field': ['val3', 'val2']},
            'third': {'field': ['val3', 'val2', 'val1']}
        }}

        docs = list(fs.collection('foo').where('field', 'array_contains', 'val1').stream())
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].to_dict(), {'field': ['val3', 'val2', 'val1']})

    def test_collection_whereArrayContainsAny(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'field': ['val4']},
            'second': {'field': ['val3', 'val2']},
            'third': {'field': ['val3', 'val2', 'val1']}
        }}

        contains_any_docs = list(fs.collection('foo').where('field', 'array_contains_any', ['val1', 'val4']).stream())
        self.assertEqual(len(contains_any_docs), 2)
        self.assertEqual({'field': ['val4']}, contains_any_docs[0].to_dict())
        self.assertEqual({'field': ['val3', 'val2', 'val1']}, contains_any_docs[1].to_dict())

    def test_collection_orderBy(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'order': 2},
            'second': {'order': 1}
        }}

        docs = list(fs.collection('foo').order_by('order').stream())
        self.assertEqual({'order': 1}, docs[0].to_dict())
        self.assertEqual({'order': 2}, docs[1].to_dict())

    def test_collection_orderBy_descending(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'order': 2},
            'second': {'order': 3},
            'third': {'order': 1}
        }}

        docs = list(fs.collection('foo').order_by('order', direction="DESCENDING").stream())
        self.assertEqual({'order': 3}, docs[0].to_dict())
        self.assertEqual({'order': 2}, docs[1].to_dict())
        self.assertEqual({'order': 1}, docs[2].to_dict())

    def test_collection_limit(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2}
        }}
        docs = list(fs.collection('foo').limit(1).stream())
        self.assertEqual({'id': 1}, docs[0].to_dict())
        self.assertEqual(1, len(docs))

    def test_collection_offset(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').offset(1).stream())

        self.assertEqual({'id': 2}, docs[0].to_dict())
        self.assertEqual({'id': 3}, docs[1].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_orderby_offset(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').order_by("id").offset(1).stream())

        self.assertEqual({'id': 2}, docs[0].to_dict())
        self.assertEqual({'id': 3}, docs[1].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_start_at(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').start_at({'id': 2}).stream())
        self.assertEqual({'id': 2}, docs[0].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_start_at_order_by(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').order_by('id').start_at({'id': 2}).stream())
        self.assertEqual({'id': 2}, docs[0].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_start_at_doc_snapshot(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3},
            'fourth': {'id': 4},
            'fifth': {'id': 5},
        }}

        doc = fs.collection('foo').document('second').get()

        docs = list(fs.collection('foo').order_by('id').start_at(doc).stream())
        self.assertEqual(4, len(docs))
        self.assertEqual({'id': 2}, docs[0].to_dict())
        self.assertEqual({'id': 3}, docs[1].to_dict())
        self.assertEqual({'id': 4}, docs[2].to_dict())
        self.assertEqual({'id': 5}, docs[3].to_dict())

    def test_collection_start_after(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').start_after({'id': 1}).stream())
        self.assertEqual({'id': 2}, docs[0].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_start_after_similar_objects(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1, 'value': 1},
            'second': {'id': 2, 'value': 2},
            'third': {'id': 3, 'value': 2},
            'fourth': {'id': 4, 'value': 3}
        }}
        docs = list(fs.collection('foo').order_by('id').start_after({'id': 3, 'value': 2}).stream())
        self.assertEqual({'id': 4, 'value': 3}, docs[0].to_dict())
        self.assertEqual(1, len(docs))

    def test_collection_start_after_order_by(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').order_by('id').start_after({'id': 2}).stream())
        self.assertEqual({'id': 3}, docs[0].to_dict())
        self.assertEqual(1, len(docs))

    def test_collection_start_after_doc_snapshot(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'second': {'id': 2},
            'third': {'id': 3},
            'fourth': {'id': 4},
            'fifth': {'id': 5},
        }}

        doc = fs.collection('foo').document('second').get()

        docs = list(fs.collection('foo').order_by('id').start_after(doc).stream())
        self.assertEqual(3, len(docs))
        self.assertEqual({'id': 3}, docs[0].to_dict())
        self.assertEqual({'id': 4}, docs[1].to_dict())
        self.assertEqual({'id': 5}, docs[2].to_dict())

    def test_collection_end_before(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').end_before({'id': 2}).stream())
        self.assertEqual({'id': 1}, docs[0].to_dict())
        self.assertEqual(1, len(docs))

    def test_collection_end_before_order_by(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').order_by('id').end_before({'id': 2}).stream())
        self.assertEqual({'id': 1}, docs[0].to_dict())
        self.assertEqual(1, len(docs))

    def test_collection_end_before_doc_snapshot(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3},
            'fourth': {'id': 4},
            'fifth': {'id': 5},
        }}

        doc = fs.collection('foo').document('fourth').get()

        docs = list(fs.collection('foo').order_by('id').end_before(doc).stream())
        self.assertEqual(3, len(docs))

        self.assertEqual({'id': 1}, docs[0].to_dict())
        self.assertEqual({'id': 2}, docs[1].to_dict())
        self.assertEqual({'id': 3}, docs[2].to_dict())

    def test_collection_end_at(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').end_at({'id': 2}).stream())
        self.assertEqual({'id': 2}, docs[1].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_end_at_order_by(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3}
        }}
        docs = list(fs.collection('foo').order_by('id').end_at({'id': 2}).stream())
        self.assertEqual({'id': 2}, docs[1].to_dict())
        self.assertEqual(2, len(docs))

    def test_collection_end_at_doc_snapshot(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1},
            'second': {'id': 2},
            'third': {'id': 3},
            'fourth': {'id': 4},
            'fifth': {'id': 5},
        }}

        doc = fs.collection('foo').document('fourth').get()

        docs = list(fs.collection('foo').order_by('id').end_at(doc).stream())
        self.assertEqual(4, len(docs))

        self.assertEqual({'id': 1}, docs[0].to_dict())
        self.assertEqual({'id': 2}, docs[1].to_dict())
        self.assertEqual({'id': 3}, docs[2].to_dict())
        self.assertEqual({'id': 4}, docs[3].to_dict())

    def test_collection_limitAndOrderBy(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'order': 2},
            'second': {'order': 1},
            'third': {'order': 3}
        }}
        docs = list(fs.collection('foo').order_by('order').limit(2).stream())
        self.assertEqual({'order': 1}, docs[0].to_dict())
        self.assertEqual({'order': 2}, docs[1].to_dict())

    def test_collection_listDocuments(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'order': 2},
            'second': {'order': 1},
            'third': {'order': 3}
        }}
        doc_refs = list(fs.collection('foo').list_documents())
        self.assertEqual(3, len(doc_refs))
        for doc_ref in doc_refs:
            self.assertIsInstance(doc_ref, DocumentReference)

    def test_collection_stream(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'order': 2},
            'second': {'order': 1},
            'third': {'order': 3}
        }}
        doc_snapshots = list(fs.collection('foo').stream())
        self.assertEqual(3, len(doc_snapshots))
        for doc_snapshot in doc_snapshots:
            self.assertIsInstance(doc_snapshot, DocumentSnapshot)

    def test_collection_parent(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'order': 2},
            'second': {'order': 1},
            'third': {'order': 3}
        }}
        doc_snapshots = fs.collection('foo').stream()
        for doc_snapshot in doc_snapshots:
            doc_reference = doc_snapshot.reference
            subcollection = doc_reference.collection('order')
            self.assertIs(subcollection.parent, doc_reference)

    def test_collection_addDocument(self):
        fs = MockFirestore()
        fs._data = {'foo': {}}
        doc_id = 'bar'
        doc_content = {'id': doc_id, 'xy': 'z'}
        timestamp, doc_ref = fs.collection('foo').add(doc_content)
        self.assertEqual(doc_content, doc_ref.get().to_dict())

        doc = fs.collection('foo').document(doc_id).get().to_dict()
        self.assertEqual(doc_content, doc)

        with self.assertRaises(AlreadyExists):
            fs.collection('foo').add(doc_content)
