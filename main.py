import argparse
import csv
import os
from typing import List, Dict, Any, Optional, Tuple


def parse_args() -> argparse.Namespace:
    """
    Парсит аргументы командной строки для обработки CSV-файла.
    :return: Пространство имён с аргументами.
    """
    parser = argparse.ArgumentParser(description='Обработка CSV файлов')
    parser.add_argument('--file', type=str, help='Путь к CSV файлу')
    parser.add_argument('--where', type=str, help='Условие фильтрации (например "price>100")')
    parser.add_argument('--aggregate', type=str, help='Агрегация (например "avg(price)")')
    return parser.parse_args()


def read_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Читает CSV-файл и возвращает список строк в виде словарей.
    :param file_path: Путь к CSV-файлу.
    :return: Список словарей, представляющих строки файла.
    :raises FileNotFoundError: Если файл не найден.
    :raises ValueError: Если путь не является файлом.
    :raises Exception: При ошибке чтения файла.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Путь не является файлом: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        raise Exception(f"Ошибка чтения файла: {e}")


def parse_filter(filter_expr: str) -> Tuple[str, str, str]:
    """
    Разбирает выражение фильтрации на колонку, оператор и значение.
    :param filter_expr: Строка фильтрации (например, 'price>100').
    :return: Кортеж (колонка, оператор, значение).
    :raises ValueError: Если выражение некорректно.
    """
    operators = ['>', '<', '=']
    for idx, char in enumerate(filter_expr):
        if char in operators:
            col = filter_expr[:idx]
            op = char
            value = filter_expr[idx + 1:]
            return col, op, value
    raise ValueError(f"Неверное условие фильтра: {filter_expr}")


def apply_filter(data: List[Dict[str, Any]], col: str, op: str, value: str) -> List[Dict[str, Any]]:
    """
    Фильтрует данные по условию (колонка, оператор, значение).
    :param data: Список строк-словарей.
    :param col: Имя колонки.
    :param op: Оператор ('=', '>', '<').
    :param value: Значение для сравнения.
    :return: Отфильтрованный список данных.
    :raises ValueError: Если колонки нет в данных.
    """
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
            if op == '=' and cell_val == cmp_val:
                filtered.append(row)
            elif op == '>' and cell_val > cmp_val:
                filtered.append(row)
            elif op == '<' and cell_val < cmp_val:
                filtered.append(row)
        else:
            cell_val = str(cell)
            cmp_val = str(value)
            if op == '=' and cell_val == cmp_val:
                filtered.append(row)
            elif op == '>' and cell_val > cmp_val:
                filtered.append(row)
            elif op == '<' and cell_val < cmp_val:
                filtered.append(row)
    return filtered


def parse_agg(agg_expr: str) -> Tuple[str, str]:
    """
    Разбирает выражение агрегации на функцию и колонку.
    :param agg_expr: Строка агрегации (например, 'avg(price)').
    :return: Кортеж (функция, колонка).
    :raises ValueError: Если выражение некорректно.
    """
    if not agg_expr.endswith(')'):
        raise ValueError(f"Неверный формат агрегации: {agg_expr}")
    func, col = agg_expr[:-1].split('(', 1)
    return func, col


def apply_agg(data: List[Dict[str, Any]], col: str, func: str) -> Optional[float]:
    """
    Применяет агрегационную функцию к колонке данных.
    :param data: Список строк-словарей.
    :param col: Имя колонки.
    :param func: Имя функции ('avg', 'min', 'max').
    :return: Результат агрегации или None, если данных нет.
    :raises ValueError: Если колонка не найдена или значения нечисловые.
    """
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


def print_table(data: List[Dict[str, Any]]) -> None:
    """
    Печатает список словарей в виде таблицы.
    :param data: Список строк-словарей.
    """
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


def print_agg_result(header: str, value: Any) -> None:
    """
    Печатает результат агрегации в виде таблицы с одной ячейкой.
    :param header: Заголовок результата.
    :param value: Значение результата.
    """
    print(header)
    print("-" * len(header))
    print(str(value))


def main() -> None:
    """
    Основная функция: связывает парсинг аргументов, чтение файла, фильтрацию, агрегацию и вывод.
    """
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