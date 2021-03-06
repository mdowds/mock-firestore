from unittest import TestCase

from google.cloud import firestore

from mockfirestore import MockFirestore, NotFound


class TestDocumentReference(TestCase):
    def test_document_get_returnsDocument(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        doc = fs.collection('foo').document('first').get()
        self.assertEqual({'id': 1}, doc.to_dict())
        self.assertEqual('first', doc.id)

    def test_document_get_documentIdEqualsKey(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        doc_ref = fs.collection('foo').document('first')
        self.assertEqual('first', doc_ref.id)

    def test_document_get_newDocumentReturnsDefaultId(self):
        fs = MockFirestore()
        doc_ref = fs.collection('foo').document()
        doc = doc_ref.get()
        self.assertNotEqual(None, doc_ref.id)
        self.assertFalse(doc.exists)

    def test_document_get_documentDoesNotExist(self):
        fs = MockFirestore()
        fs._data = {'foo': {}}
        doc = fs.collection('foo').document('bar').get().to_dict()
        self.assertEqual({}, doc)

    def test_get_nestedDocument(self):
        fs = MockFirestore()
        fs._data = {'top_collection': {
            'top_document': {
                'id': 1,
                'nested_collection': {
                    'nested_document': {'id': 1.1}
                }
            }
        }}
        doc = fs.collection('top_collection')\
            .document('top_document')\
            .collection('nested_collection')\
            .document('nested_document')\
            .get().to_dict()

        self.assertEqual({'id': 1.1}, doc)

    def test_get_nestedDocument_documentDoesNotExist(self):
        fs = MockFirestore()
        fs._data = {'top_collection': {
            'top_document': {
                'id': 1,
                'nested_collection': {}
            }
        }}
        doc = fs.collection('top_collection')\
            .document('top_document')\
            .collection('nested_collection')\
            .document('nested_document')\
            .get().to_dict()

        self.assertEqual({}, doc)

    def test_document_set_setsContentOfDocument(self):
        fs = MockFirestore()
        fs._data = {'foo': {}}
        doc_content = {'id': 'bar'}
        fs.collection('foo').document('bar').set(doc_content)
        doc = fs.collection('foo').document('bar').get().to_dict()
        self.assertEqual(doc_content, doc)

    def test_document_set_mergeNewValue(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        fs.collection('foo').document('first').set({'updated': True}, merge=True)
        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual({'id': 1, 'updated': True}, doc)

    def test_document_set_mergeNewValueForNonExistentDoc(self):
        fs = MockFirestore()
        fs.collection('foo').document('first').set({'updated': True}, merge=True)
        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual({'updated': True}, doc)

    def test_document_set_overwriteValue(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        fs.collection('foo').document('first').set({'new_id': 1}, merge=False)
        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual({'new_id': 1}, doc)

    def test_document_set_isolation(self):
        fs = MockFirestore()
        fs._data = {'foo': {}}
        doc_content = {'id': 'bar'}
        fs.collection('foo').document('bar').set(doc_content)
        doc_content['id'] = 'new value'
        doc = fs.collection('foo').document('bar').get().to_dict()
        self.assertEqual({'id': 'bar'}, doc)

    def test_document_update_addNewValue(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        fs.collection('foo').document('first').update({'updated': True})
        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual({'id': 1, 'updated': True}, doc)

    def test_document_update_changeExistingValue(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        fs.collection('foo').document('first').update({'id': 2})
        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual({'id': 2}, doc)
    
    def test_document_update_documentDoesNotExist(self):
        fs = MockFirestore()
        with self.assertRaises(NotFound):
            fs.collection('foo').document('nonexistent').update({'id': 2})
        docsnap = fs.collection('foo').document('nonexistent').get()
        self.assertFalse(docsnap.exists)

    def test_document_update_isolation(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'nested': {'id': 1}}
        }}
        update_doc = {'nested': {'id': 2}}
        fs.collection('foo').document('first').update(update_doc)
        update_doc['nested']['id'] = 3
        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual({'nested': {'id': 2}}, doc)

    def test_document_update_transformerIncrementBasic(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'count': 1}
        }}
        fs.collection('foo').document('first').update({'count': firestore.Increment(2)})

        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual(doc, {'count': 3})

    def test_document_update_transformerIncrementNested(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {
                'nested': {'count': 1},
                'other': {'likes': 0},
            }
        }}
        fs.collection('foo').document('first').update({
            'nested': {'count': firestore.Increment(-1)},
            'other': {'likes': firestore.Increment(1), 'smoked': 'salmon'},
        })

        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual(doc, {
            'nested': {'count': 0},
            'other': {'likes': 1, 'smoked': 'salmon'}
        })

    def test_document_update_transformerIncrementNonExistent(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'spicy': 'tuna'}
        }}
        fs.collection('foo').document('first').update({'count': firestore.Increment(1)})

        doc = fs.collection('foo').document('first').get().to_dict()
        self.assertEqual(doc, {'count': 1, 'spicy': 'tuna'})

    def test_document_delete_documentDoesNotExistAfterDelete(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        fs.collection('foo').document('first').delete()
        doc = fs.collection('foo').document('first').get()
        self.assertEqual(False, doc.exists)

    def test_document_parent(self):
        fs = MockFirestore()
        fs._data = {'foo': {
            'first': {'id': 1}
        }}
        coll = fs.collection('foo')
        document = coll.document('first')
        self.assertIs(document.parent, coll)

