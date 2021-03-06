# Copyright 2011-2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test the pymongo common module."""

import os
import sys
import unittest
import warnings

sys.path[0:0] = [""]

from nose.plugins.skip import SkipTest

from bson.objectid import ObjectId
from bson.son import SON
from pymongo.connection import Connection
from pymongo.mongo_client import MongoClient
from pymongo.replica_set_connection import ReplicaSetConnection
from pymongo.mongo_replica_set_client import MongoReplicaSetClient
from pymongo.errors import ConfigurationError, OperationFailure
from test.utils import drop_collections


host = os.environ.get("DB_IP", 'localhost')
port = int(os.environ.get("DB_PORT", 27017))
pair = '%s:%d' % (host, port)


class TestCommon(unittest.TestCase):

    def test_baseobject(self):

        # In Python 2.6+ we could use the catch_warnings context
        # manager to test this warning nicely. As we can't do that
        # we must test raising errors before the ignore filter is applied.
        warnings.simplefilter("error", UserWarning)
        self.assertRaises(UserWarning, lambda:
                MongoClient(host, port, wtimeout=1000, w=0))
        try:
            MongoClient(host, port, wtimeout=1000, w=1)
        except UserWarning:
            self.fail()

        try:
            MongoClient(host, port, wtimeout=1000)
        except UserWarning:
            self.fail()

        warnings.resetwarnings()

        warnings.simplefilter("ignore")

        c = Connection(pair)
        self.assertFalse(c.slave_okay)
        self.assertFalse(c.safe)
        self.assertEqual({}, c.get_lasterror_options())
        db = c.test
        db.drop_collection("test")
        self.assertFalse(db.slave_okay)
        self.assertFalse(db.safe)
        self.assertEqual({}, db.get_lasterror_options())
        coll = db.test
        self.assertFalse(coll.slave_okay)
        self.assertFalse(coll.safe)
        self.assertEqual({}, coll.get_lasterror_options())
        cursor = coll.find()
        self.assertFalse(cursor._Cursor__slave_okay)
        cursor = coll.find(slave_okay=True)
        self.assertTrue(cursor._Cursor__slave_okay)

        # Setting any safe operations overrides explicit safe
        self.assertTrue(Connection(host, port, wtimeout=1000, safe=False).safe)

        c = Connection(pair, slaveok=True, w='majority',
                                     wtimeout=300, fsync=True, j=True)
        self.assertTrue(c.slave_okay)
        self.assertTrue(c.safe)
        d = {'w': 'majority', 'wtimeout': 300, 'fsync': True, 'j': True}
        self.assertEqual(d, c.get_lasterror_options())
        db = c.test
        self.assertTrue(db.slave_okay)
        self.assertTrue(db.safe)
        self.assertEqual(d, db.get_lasterror_options())
        coll = db.test
        self.assertTrue(coll.slave_okay)
        self.assertTrue(coll.safe)
        self.assertEqual(d, coll.get_lasterror_options())
        cursor = coll.find()
        self.assertTrue(cursor._Cursor__slave_okay)
        cursor = coll.find(slave_okay=False)
        self.assertFalse(cursor._Cursor__slave_okay)

        c = Connection('mongodb://%s/?'
                       'w=2;wtimeoutMS=300;fsync=true;'
                       'journal=true' % (pair,))
        self.assertTrue(c.safe)
        d = {'w': 2, 'wtimeout': 300, 'fsync': True, 'j': True}
        self.assertEqual(d, c.get_lasterror_options())

        c = Connection('mongodb://%s/?'
                       'slaveok=true;w=1;wtimeout=300;'
                       'fsync=true;j=true' % (pair,))
        self.assertTrue(c.slave_okay)
        self.assertTrue(c.safe)
        d = {'w': 1, 'wtimeout': 300, 'fsync': True, 'j': True}
        self.assertEqual(d, c.get_lasterror_options())
        self.assertEqual(d, c.write_concern)
        db = c.test
        self.assertTrue(db.slave_okay)
        self.assertTrue(db.safe)
        self.assertEqual(d, db.get_lasterror_options())
        self.assertEqual(d, db.write_concern)
        coll = db.test
        self.assertTrue(coll.slave_okay)
        self.assertTrue(coll.safe)
        self.assertEqual(d, coll.get_lasterror_options())
        self.assertEqual(d, coll.write_concern)
        cursor = coll.find()
        self.assertTrue(cursor._Cursor__slave_okay)
        cursor = coll.find(slave_okay=False)
        self.assertFalse(cursor._Cursor__slave_okay)

        c.unset_lasterror_options()
        self.assertTrue(c.slave_okay)
        self.assertTrue(c.safe)
        c.safe = False
        self.assertFalse(c.safe)
        c.slave_okay = False
        self.assertFalse(c.slave_okay)
        self.assertEqual({}, c.get_lasterror_options())
        self.assertEqual({}, c.write_concern)
        db = c.test
        self.assertFalse(db.slave_okay)
        self.assertFalse(db.safe)
        self.assertEqual({}, db.get_lasterror_options())
        self.assertEqual({}, db.write_concern)
        coll = db.test
        self.assertFalse(coll.slave_okay)
        self.assertFalse(coll.safe)
        self.assertEqual({}, coll.get_lasterror_options())
        self.assertEqual({}, coll.write_concern)
        cursor = coll.find()
        self.assertFalse(cursor._Cursor__slave_okay)
        cursor = coll.find(slave_okay=True)
        self.assertTrue(cursor._Cursor__slave_okay)

        coll.set_lasterror_options(j=True)
        self.assertEqual({'j': True}, coll.get_lasterror_options())
        self.assertEqual({'j': True}, coll.write_concern)
        self.assertEqual({}, db.get_lasterror_options())
        self.assertEqual({}, db.write_concern)
        self.assertFalse(db.safe)
        self.assertEqual({}, c.get_lasterror_options())
        self.assertEqual({}, c.write_concern)
        self.assertFalse(c.safe)

        db.set_lasterror_options(w='majority')
        self.assertEqual({'j': True}, coll.get_lasterror_options())
        self.assertEqual({'j': True}, coll.write_concern)
        self.assertEqual({'w': 'majority'}, db.get_lasterror_options())
        self.assertEqual({'w': 'majority'}, db.write_concern)
        self.assertEqual({}, c.get_lasterror_options())
        self.assertEqual({}, c.write_concern)
        self.assertFalse(c.safe)
        db.slave_okay = True
        self.assertTrue(db.slave_okay)
        self.assertFalse(c.slave_okay)
        self.assertFalse(coll.slave_okay)
        cursor = coll.find()
        self.assertFalse(cursor._Cursor__slave_okay)
        cursor = db.coll2.find()
        self.assertTrue(cursor._Cursor__slave_okay)
        cursor = db.coll2.find(slave_okay=False)
        self.assertFalse(cursor._Cursor__slave_okay)

        self.assertRaises(ConfigurationError, coll.set_lasterror_options, foo=20)
        self.assertRaises(TypeError, coll._BaseObject__set_slave_okay, 20)
        self.assertRaises(TypeError, coll._BaseObject__set_safe, 20)

        coll.remove()
        self.assertEqual(None, coll.find_one(slave_okay=True))
        coll.unset_lasterror_options()
        coll.set_lasterror_options(w=4, wtimeout=10)
        # Fails if we don't have 4 active nodes or we don't have replication...
        self.assertRaises(OperationFailure, coll.insert, {'foo': 'bar'})
        # Succeeds since we override the lasterror settings per query.
        self.assertTrue(coll.insert({'foo': 'bar'}, fsync=True))
        drop_collections(db)

        warnings.resetwarnings()

    def test_write_concern(self):
        c = Connection(pair)

        self.assertEqual({}, c.write_concern)
        wc = {'w': 2, 'wtimeout': 1000}
        c.write_concern = wc
        self.assertEqual(wc, c.write_concern)
        wc = {'w': 3, 'wtimeout': 1000}
        c.write_concern['w'] = 3
        self.assertEqual(wc, c.write_concern)
        wc = {'w': 3}
        del c.write_concern['wtimeout']
        self.assertEqual(wc, c.write_concern)

        wc = {'w': 3, 'wtimeout': 1000}
        c = Connection(w=3, wtimeout=1000)
        self.assertEqual(wc, c.write_concern)
        wc = {'w': 2, 'wtimeout': 1000}
        c.write_concern = wc
        self.assertEqual(wc, c.write_concern)

        db = c.test
        self.assertEqual(wc, db.write_concern)
        coll = db.test
        self.assertEqual(wc, coll.write_concern)
        coll.write_concern = {'j': True}
        self.assertEqual({'j': True}, coll.write_concern)
        self.assertEqual(wc, db.write_concern)

        wc = SON([('w', 2)])
        coll.write_concern = wc
        self.assertEqual(wc.to_dict(), coll.write_concern)

        def f():
            c.write_concern = {'foo': 'bar'}
        self.assertRaises(ConfigurationError, f)

        def f():
            c.write_concern['foo'] = 'bar'
        self.assertRaises(ConfigurationError, f)

        def f():
            c.write_concern = [('foo', 'bar')]
        self.assertRaises(ConfigurationError, f)

    def test_connection(self):
        c = Connection(pair)
        coll = c.pymongo_test.write_concern_test
        coll.drop()
        doc = {"_id": ObjectId()}
        coll.insert(doc)
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertTrue(coll.insert(doc))
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        c = Connection(pair, safe=True)
        coll = c.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertRaises(OperationFailure, coll.insert, doc)
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        c = Connection("mongodb://%s/" % (pair,))
        self.assertFalse(c.safe)
        coll = c.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc))
        c = Connection("mongodb://%s/?safe=true" % (pair,))
        self.assertTrue(c.safe)
        coll = c.pymongo_test.write_concern_test
        self.assertRaises(OperationFailure, coll.insert, doc)

    def test_mongo_client(self):
        m = MongoClient(pair, w=0)
        coll = m.pymongo_test.write_concern_test
        coll.drop()
        doc = {"_id": ObjectId()}
        coll.insert(doc)
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertTrue(coll.insert(doc))
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        m = MongoClient(pair)
        coll = m.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertRaises(OperationFailure, coll.insert, doc)
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        m = MongoClient("mongodb://%s/" % (pair,))
        self.assertTrue(m.safe)
        coll = m.pymongo_test.write_concern_test
        self.assertRaises(OperationFailure, coll.insert, doc)
        m = MongoClient("mongodb://%s/?w=0" % (pair,))
        self.assertFalse(m.safe)
        coll = m.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc))

    def test_replica_set_connection(self):
        c = Connection(pair)
        ismaster = c.admin.command('ismaster')
        if 'setName' in ismaster:
            setname = str(ismaster.get('setName'))
        else:
            raise SkipTest("Not connected to a replica set.")
        c = ReplicaSetConnection(pair, replicaSet=setname)
        coll = c.pymongo_test.write_concern_test
        coll.drop()
        doc = {"_id": ObjectId()}
        coll.insert(doc)
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertTrue(coll.insert(doc))
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        c = ReplicaSetConnection(pair, replicaSet=setname, safe=True)
        coll = c.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertRaises(OperationFailure, coll.insert, doc)
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        c = ReplicaSetConnection("mongodb://%s/?replicaSet=%s" % (pair, setname))
        self.assertFalse(c.safe)
        coll = c.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc))
        c = ReplicaSetConnection("mongodb://%s/?replicaSet=%s;safe=true" % (pair, setname))
        self.assertTrue(c.safe)
        coll = c.pymongo_test.write_concern_test
        self.assertRaises(OperationFailure, coll.insert, doc)

    def test_mongo_replica_set_client(self):
        c = Connection(pair)
        ismaster = c.admin.command('ismaster')
        if 'setName' in ismaster:
            setname = str(ismaster.get('setName'))
        else:
            raise SkipTest("Not connected to a replica set.")
        m = MongoReplicaSetClient(pair, replicaSet=setname, w=0)
        coll = m.pymongo_test.write_concern_test
        coll.drop()
        doc = {"_id": ObjectId()}
        coll.insert(doc)
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertTrue(coll.insert(doc))
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        m = MongoReplicaSetClient(pair, replicaSet=setname)
        coll = m.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc, safe=False))
        self.assertTrue(coll.insert(doc, w=0))
        self.assertRaises(OperationFailure, coll.insert, doc)
        self.assertRaises(OperationFailure, coll.insert, doc, safe=True)
        self.assertRaises(OperationFailure, coll.insert, doc, w=1)

        m = MongoReplicaSetClient("mongodb://%s/?replicaSet=%s" % (pair, setname))
        self.assertTrue(m.safe)
        coll = m.pymongo_test.write_concern_test
        self.assertRaises(OperationFailure, coll.insert, doc)
        m = MongoReplicaSetClient("mongodb://%s/?replicaSet=%s;w=0" % (pair, setname))
        self.assertFalse(m.safe)
        coll = m.pymongo_test.write_concern_test
        self.assertTrue(coll.insert(doc))


if __name__ == "__main__":
    unittest.main()
