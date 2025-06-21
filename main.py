import argparse
import csv
import os


def parse_args():
    parser = argparse.ArgumentParser(description='Обработка CSV файлов')
    parser.add_argument('--file', type=str, help='Путь к CSV файлу')
    parser.add_argument('--where', type=str, help='Условие фильтрации (например "price>100")')
    parser.add_argument('--aggregate', type=str, help='Агрегация (например "avg(price)")')
    parser.add_argument('--order-by, ')
    return parser.parse_args()


def read_csv(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Путь не является файлом: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        raise Exception(f"Ошибка чтения файла: {e}")


def parse_filter(filter_expr):
    operators = ['>', '<', '=']
    for idx, char in enumerate(filter_expr):
        if char in operators:
            col = filter_expr[:idx]
            op = char
            value = filter_expr[idx + 1:]
            return col, op, value
    raise ValueError(f"Неверное условие фильтра: {filter_expr}")


def apply_filter(data, col, op, value):
    if not data:
        return data
    if col not in data[0]:
        raise ValueError(f"Колонка не найдена: {col}")

    try:
        value_float = float(value)
        use_float = True
    except ValueError:
        use_float = False

    filtered = []
    for row in data:
        cell = row[col]
        if use_float:
            try:
                cell_val = float(cell)
            except ValueError:
                continue
            cmp_val = value_float
        else:
            cell_val = cell
            cmp_val = value

        if op == '=' and cell_val == cmp_val:
            filtered.append(row)
        elif op == '>' and cell_val > cmp_val:
            filtered.append(row)
        elif op == '<' and cell_val < cmp_val:
            filtered.append(row)
    return filtered


def parse_agg(agg_expr):
    if not agg_expr.endswith(')'):
        raise ValueError(f"Неверный формат агрегации: {agg_expr}")
    func, col = agg_expr[:-1].split('(', 1)
    return func, col


def apply_agg(data, col, func):
    if not data:
        return None
    if col not in data[0]:
        raise ValueError(f"Колонка не найдена: {col}")

    values = []
    for row in data:
        try:
            values.append(float(row[col]))
        except ValueError:
            raise ValueError(f"Нечисловое значение в колонке {col}: {row[col]}")

    if func == 'avg':
        return round(sum(values) / len(values), 2)
    elif func == 'min':
        return min(values)
    elif func == 'max':
        return max(values)
    else:
        raise ValueError(f"Неизвестная функция агрегации: {func}")


def print_table(data):
    """Печатает список словарей в виде таблицы"""
    if not data:
        print("Нет данных для отображения")
        return

    # Получаем заголовки
    headers = list(data[0].keys())

    # Вычисляем максимальную ширину для каждого столбца
    col_widths = {}
    for header in headers:
        max_width = len(header)
        for row in data:
            if header in row:
                value_len = len(str(row[header]))
                if value_len > max_width:
                    max_width = value_len
        col_widths[header] = max_width

    # Печатаем заголовки
    header_line = " | ".join([header.ljust(col_widths[header]) for header in headers])
    print(header_line)
    print("-" * len(header_line))

    # Печатаем строки данных
    for row in data:
        row_line = " | ".join([str(row.get(header, "")).ljust(col_widths[header]) for header in headers])
        print(row_line)


def print_agg_result(header, value):
    """Печатает результат агрегации в виде таблицы с одной ячейкой"""
    print(header)
    print("-" * len(header))
    print(str(value))


def main():
    args = parse_args()

    try:
        data = read_csv(args.file)
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    if args.where:
        try:
            col, op, value = parse_filter(args.where)
            data = apply_filter(data, col, op, value)
        except ValueError as e:
            print(f"Ошибка фильтрации: {e}")
            return

    if args.aggregate:
        try:
            func, col = parse_agg(args.aggregate)
            result = apply_agg(data, col, func)
        except ValueError as e:
            print(f"Ошибка агрегации: {e}")
            return

        if result is None:
            print("Нет данных для агрегации")
        else:
            header = f"{func}({col})"
            print_agg_result(header, result)
    else:
        print_table(data)


if __name__ == "__main__":
    main()