VERSION = '0.9'

import argparse
import csv
import json
import os
import re
from datetime import datetime

DATE_PATTERN = re.compile(r"\d{2}\.\d{2}\.\d{2}$")
REGION_PATTERN = r"(?:🇷🇺|🇪🇺|🇨🇳|🇬🇧)"


def select_date_dirs(base_dir: str = "."):
    """Return two latest date directories under base_dir."""
    dirs = [d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d)) and DATE_PATTERN.match(d)]
    if len(dirs) < 2:
        print(f"Ошибка: обнаружено только {len(dirs)} папка(и) с датами, минимум две.")
        raise SystemExit(1)
    dirs.sort(key=lambda x: datetime.strptime(x, "%d.%m.%y"))
    return [os.path.join(base_dir, d) for d in dirs[-2:]]


def collect_txt_files(dirs):
    files = []
    for d in dirs:
        for name in os.listdir(d):
            if name.lower().endswith('.txt'):
                files.append(os.path.join(d, name))
    return files


MEMORY_RE = r"(?:\d+/\d+(?:gb|GB)?|\d+(?:gb|GB))"
LINE_RE = re.compile(
    rf"^(?P<model>.+?)\s*(?P<region>{REGION_PATTERN})?\s*(?P<memory>{MEMORY_RE})\s+(?P<color>.+?)\s*-?\s*(?P<price>\d+)\s*$"
)


def parse_file_sections(file_path):
    records = []
    try:
        with open(file_path, encoding='utf-8') as f:
            lines = f.read().splitlines()
    except Exception as e:
        print(f"Ошибка чтения файла {file_path}: {e}")
        return records

    source = os.path.basename(file_path)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('ПРАЙС'):
            source = line.split(' ', 1)[1].strip() if ' ' in line else line
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        model = m.group('model').strip()
        region = m.group('region') or ''
        memory = m.group('memory')
        memory = memory.lower().replace('gb', '')
        color = m.group('color').strip().title()
        price = int(m.group('price'))
        records.append({
            'model': model,
            'region': region,
            'memory': memory,
            'color': color,
            'price': price,
            'source': source
        })
    return records


def group_positions(records):
    grouped = {}
    for rec in records:
        key = (rec['model'], rec['region'], rec['memory'], rec['color'])
        if key not in grouped or rec['price'] < grouped[key]['price']:
            grouped[key] = rec
    return list(grouped.values())


def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(data, path):
    header = ['Модель', 'Регион', 'Память', 'Цвет', 'Цена', 'Источник']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for rec in data:
            writer.writerow([
                rec['model'], rec['region'], rec['memory'],
                rec['color'], rec['price'], rec['source']
            ])


def compare_prev(curr, prev):
    curr_keys = { (r['model'], r['region'], r['memory'], r['color']) : r for r in curr }
    prev_keys = { (r['model'], r['region'], r['memory'], r['color']) : r for r in prev }
    new = [curr_keys[k] for k in curr_keys.keys() - prev_keys.keys()]
    removed = [prev_keys[k] for k in prev_keys.keys() - curr_keys.keys()]
    return new, removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lists', nargs='+', help='Список прайсов')
    parser.add_argument('--prev', help='Файл предыдущего дня')
    parser.add_argument('--out_curr', default='curr_data.json')
    parser.add_argument('--report', default='min_prices_report.csv')
    args = parser.parse_args()

    if args.lists:
        txt_files = args.lists
    else:
        dirs = select_date_dirs()
        txt_files = collect_txt_files(dirs)
    if not txt_files:
        print('Ошибка: .txt файлы не найдены')
        raise SystemExit(1)

    all_records = []
    for path in txt_files:
        all_records.extend(parse_file_sections(path))

    grouped = group_positions(all_records)

    os.makedirs('Отчеты', exist_ok=True)
    curr_json = os.path.join('Отчеты', args.out_curr)
    report_csv = os.path.join('Отчеты', args.report)

    save_json(grouped, curr_json)
    save_csv(grouped, report_csv)

    if args.prev:
        try:
            with open(args.prev, encoding='utf-8') as f:
                prev_data = json.load(f)
        except Exception as e:
            print(f"Ошибка чтения файла {args.prev}: {e}")
            prev_data = []
        new, removed = compare_prev(grouped, prev_data)
        new_csv = os.path.join('Отчеты', 'new_positions_report.csv')
        removed_csv = os.path.join('Отчеты', 'removed_positions_report.csv')
        save_csv(new, new_csv)
        save_csv(removed, removed_csv)


if __name__ == '__main__':
    main()
