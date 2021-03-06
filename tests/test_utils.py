#!/usr/bin/env python3

import pytest  # type: ignore
import os
import time
import random
import pathlib
import numpy as np  # type: ignore
from glob import iglob
import rtCommon.utils as utils  # type: ignore
import rtCommon.validationUtils as vutils  # type: ignore
from rtCommon.structDict import MatlabStructDict  # type: ignore


@pytest.fixture(scope="module")
def matTestFilename():  # type: ignore
    return os.path.join(os.path.dirname(__file__), 'test_input/teststruct.mat')


class TestFindNewestFile:
    TEST_BASE_FILENAME = '/tmp/testdir/file1_20170101T01010'
    NUM_TEST_FILES = 5

    def setup_class(cls):
        # create tmp directory if it doesn't exist
        pathlib.Path('/tmp/testdir/').mkdir(parents=True, exist_ok=True)
        # check if test files already exist, get the count of them
        count_testfiles = sum(1 for _ in iglob(TestFindNewestFile.TEST_BASE_FILENAME + "*"))
        if count_testfiles != TestFindNewestFile.NUM_TEST_FILES:
            # remove any existing testfiles
            for filename in iglob(TestFindNewestFile.TEST_BASE_FILENAME + "*"):
                os.remove(filename)
            # create the correct number of test files
            for i in range(TestFindNewestFile.NUM_TEST_FILES):
                filename = TestFindNewestFile.TEST_BASE_FILENAME + str(i)
                with open(filename, 'w') as fp:
                    fp.write("test file")
                    time.sleep(1)

    def assert_result_matches_filename(self, filename):
        assert filename == (self.TEST_BASE_FILENAME + str(self.NUM_TEST_FILES - 1))

    def test_normalCase(self):
        print("Test findNewestFile normal case:")
        filename = utils.findNewestFile('/tmp/testdir', 'file1_20170101*')
        self.assert_result_matches_filename(filename)

    def test_emptyPath(self):
        print("Test findNewestFile empty path:")
        filename = utils.findNewestFile('', '/tmp/testdir/file1_20170101*')
        self.assert_result_matches_filename(filename)

    def test_pathInPattern(self):
        print("Test findNewestFile path embedded in pattern:")
        filename = utils.findNewestFile(
            '/tmp/testdir', '/tmp/testdir/file1_20170101*')
        self.assert_result_matches_filename(filename)

    def test_pathPartiallyInPattern(self):
        print("Test findNewestFile path partially in pattern:")
        filename = utils.findNewestFile('/tmp', 'testdir/file1_20170101*')
        self.assert_result_matches_filename(filename)

    def test_noMatchingFiles(self):
        print("Test findNewestFile no matching files:")
        filename = utils.findNewestFile('/tmp/testdir/', 'no_such_file')
        assert filename is None


class TestCompareArrays:
    A = None
    B = None
    max_deviation = .01

    def setup_class(cls):
        arrayDims = [40, 50, 60]
        A = np.random.random(arrayDims)
        delta = np.random.random(arrayDims) * TestCompareArrays.max_deviation
        B = A + (A * delta)
        TestCompareArrays.A = A
        TestCompareArrays.B = B

    def test_compareArrays(self):
        print("Test compareArrays")
        # import pdb; pdb.set_trace()
        result = vutils.compareArrays(self.B, self.A)
        assert result['mean'] < 2 / 3 * self.max_deviation
        assert result['max'] < self.max_deviation
        return

    def test_areArraysClose(self):
        print("Test areArraysClose")
        max_mean = 2 / 3 * self.max_deviation
        assert vutils.areArraysClose(self.B, self.A, mean_limit=max_mean)
        return


class TestCompareMatStructs:
    A = None
    B = None
    max_deviation = .01

    def setup_class(cls):
        def delta(val):
            return val + (val * random.random() * TestCompareMatStructs.max_deviation)
        A = MatlabStructDict(
            {'sub': MatlabStructDict({})}, 'sub')
        A.str1 = "hello"
        A.a1 = 6.0
        A.sub.a2 = np.array([1, 2, 3, 4, 5], dtype=np.float)
        A.sub.b2 = 7.0
        A.sub.str2 = "world"
        B = MatlabStructDict(
            {'sub': MatlabStructDict({})}, 'sub')
        B.str1 = "hello"
        B.a1 = delta(A.a1)
        B.sub.a2 = delta(A.a2)
        B.sub.b2 = delta(A.b2)
        B.sub.str2 = "world"
        TestCompareMatStructs.A = A
        TestCompareMatStructs.B = B

    def test_compareMatStructs_all_fields(self):
        print("Test compareMatStructs_all_fields")
        result = vutils.compareMatStructs(self.A, self.B)
        means = [result[key]['mean'] for key in result.keys()]
        assert len(means) == 5
        assert all(mean < self.max_deviation for mean in means)

    def test_compareMatStructs_field_subset(self):
        print("Test compareMatStructs_field_subset")
        result = vutils.compareMatStructs(self.A, self.B, ['a2', 'str1'])
        means = [result[key]['mean'] for key in result.keys()]
        assert len(means) == 2
        assert all(mean < self.max_deviation for mean in means)

    def test_isMeanWithinThreshold(self):
        a = {'val1': {'mean': .1, 'max': .2},
             'val2': {'mean': .05, 'max': .075}}
        assert vutils.isMeanWithinThreshold(a, .11)
        assert not vutils.isMeanWithinThreshold(a, .09)


class TestCompareMatFiles:
    def test_compareMatFiles(self, matTestFilename):
        res = vutils.compareMatFiles(matTestFilename, matTestFilename)
        assert vutils.isMeanWithinThreshold(res, 0)


class TestPearsonsMeanCorr:
    def test_pearsonsMeanCorr(self):
        n1 = np.array([[1, 2, 3, 4, 5],
                       [np.nan, np.nan, np.nan, np.nan, np.nan]])
        n2 = np.array([[1.1, 2.1, 3.2, 4.1, 5.05],
                       [np.nan, np.nan, np.nan, np.nan, np.nan]])
        n1t = np.transpose(n1)
        n2t = np.transpose(n2)
        res = vutils.pearsons_mean_corr(n1t, n2t)
        assert res > 0.999


if __name__ == "__main__":
    print("PYTEST MAIN:")
    pytest.main()
