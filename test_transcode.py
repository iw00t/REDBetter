# coding=utf-8
import unittest
import transcode


class TestGetSuitableBasename(unittest.TestCase):
    def test_ascii(self):
        name = 'Artist - Album (2000) [FLAC]'
        expected = name
        actual = transcode.get_suitable_basename(name)
        self.assertEqual(expected, actual)

    def test_japanese(self):
        name = u'Nihon Kogakuin College (日本工学院専門学校) - (1985) Pink Papaia {NKS MD8503A 24-96 Vinyl} [FLAC]'
        expected = name
        actual = transcode.get_suitable_basename(name)
        self.assertEqual(expected, actual)

    def test_illegal_characters(self):
        name = 'fi:l*e/p\"a?t>h|.t<xt \0_abc<d>e%f/(g)h+i_0.txt'
        expected = 'fi,lepath.txt _abcde%f(g)h+i_0.txt'
        actual = transcode.get_suitable_basename(name)
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
