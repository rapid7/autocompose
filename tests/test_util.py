import unittest
from autocompose.util import Util


class TestReplaceTemplateVariables(unittest.TestCase):

    def test_replace(self):
        self.assertEqual(4, Util.replace_template_variables(3, {3: 4}))
        self.assertEqual([1, 2, 4], Util.replace_template_variables([1, 2, 3], {3: 4}))
        self.assertEqual({1: 2, 3: 5}, Util.replace_template_variables({1: 2, 3: '4'}, {'4': 5}))
        self.assertRaises(TypeError, Util.replace_template_variables, [3, 'not a dictionary'])


class TestDeepMerge(unittest.TestCase):

    def test_1(self):

        a = {'a': '1'}
        b = {'b': '2'}

        self.assertEqual({'a': '1', 'b': '2'}, Util.deep_merge(a, b))

        a = {'a': '1'}
        c = {'a': '2'}

        self.assertEqual(c, Util.deep_merge(a, c))

        self.assertEqual([1, 2, 3, 4, 5], Util.deep_merge([1, 2, 3], [3, 4, 5]))
        self.assertEqual(4, Util.deep_merge(5, 4))

        d = {'a': 1, 'b': [1, 2, 3, 4, 5], 'c': {'a': 1, 'b': [1, 2, 3, 4, 5]}}
        e = {'d': 2, 'b': [6, 7], 'c': {'c': 1, 'd': [1, 2]}}
        merged = {'a': 1, 'd': 2, 'b': [1, 2, 3, 4, 5, 6, 7], 'c': {'a': 1, 'b': [1, 2, 3, 4, 5], 'c': 1, 'd': [1, 2]}}
        self.assertEqual(merged, Util.deep_merge(d, e))


if __name__ == '__main__':
    unittest.main()
