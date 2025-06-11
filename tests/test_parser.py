import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import os
import unittest
from tempfile import TemporaryDirectory

import xiaomi_price_parser as xpp

class TestSelectDateDirs(unittest.TestCase):
    def test_no_dirs(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                xpp.select_date_dirs(tmp)

    def test_one_dir(self):
        with TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, '01.01.24'))
            with self.assertRaises(SystemExit):
                xpp.select_date_dirs(tmp)

    def test_two_latest(self):
        with TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, '01.01.24'))
            os.mkdir(os.path.join(tmp, '02.01.24'))
            os.mkdir(os.path.join(tmp, '03.01.24'))
            latest = xpp.select_date_dirs(tmp)
            self.assertEqual(sorted(latest),
                             sorted([os.path.join(tmp,'02.01.24'), os.path.join(tmp,'03.01.24')]))

class TestParseFileSections(unittest.TestCase):
    SAMPLE = (
        'ПРАЙС T87\n'
        'Model A 🇷🇺 12/256 Black-12000\n'
        'Model A 🇪🇺 12/256 white -13000\n'
        'Xiaomi 13 🇷🇺 12/512 Blue-15000\n'
    )

    def test_parse(self):
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'f.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.SAMPLE)
            records = xpp.parse_file_sections(path)
            self.assertEqual(len(records), 3)
            self.assertEqual(records[0]['memory'], '12/256')
            self.assertEqual(records[0]['color'], 'Black')
            self.assertEqual(records[1]['price'], 13000)
            self.assertEqual(records[2]['model'], 'Xiaomi 13')
            self.assertEqual(records[2]['memory'], '12/512')

class TestGroupPositions(unittest.TestCase):
    def test_min_price(self):
        recs = [
            {'model':'A','region':'','memory':'12/256','color':'Black','price':100,'source':'s1'},
            {'model':'A','region':'','memory':'12/256','color':'Black','price':90,'source':'s2'},
            {'model':'A','region':'','memory':'12/256','color':'White','price':110,'source':'s1'},
        ]
        grouped = xpp.group_positions(recs)
        # Should have two groups: Black and White
        self.assertEqual(len(grouped),2)
        prices = { (r['color']): r['price'] for r in grouped }
        self.assertEqual(prices['Black'], 90)
        self.assertEqual(prices['White'], 110)

if __name__ == '__main__':
    unittest.main()
