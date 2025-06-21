import pytest
import os
import csv
import tempfile
from main import parse_args, read_csv, parse_filter, apply_filter, parse_agg, apply_agg, main

class TestCSVProcessor:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Создаем временный CSV файл
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv')
        self.csv_path = self.temp_csv.name
        csv_writer = csv.writer(self.temp_csv)
        csv_writer.writerow(['product', 'price', 'stock'])
        csv_writer.writerow(['Apple', '100', '50'])
        csv_writer.writerow(['Banana', '50', '100'])
        csv_writer.writerow(['Orange', '75', '75'])
        csv_writer.writerow(['Milk', '120', '30'])
        self.temp_csv.close()
        yield
        # Удаляем временный файл после тестов
        os.unlink(self.csv_path)

    def test_parse_args(self, monkeypatch):
        # Тест парсинга аргументов
        monkeypatch.setattr('sys.argv', ['main.py', '--file', 'data.csv', '--where', 'price>100', '--aggregate', 'avg(price)'])
        args = parse_args()
        assert args.file == 'data.csv'
        assert args.where == 'price>100'
        assert args.aggregate == 'avg(price)'

    def test_read_csv_valid(self):
        # Тест чтения CSV
        data = read_csv(self.csv_path)
        assert len(data) == 4
        assert data[0]['product'] == 'Apple'
        assert data[1]['price'] == '50'

    def test_read_csv_file_not_found(self):
        # Тест отсутствия файла
        with pytest.raises(FileNotFoundError):
            read_csv('invalid_path.csv')

    def test_read_csv_not_file(self, tmp_path):
        # Тест передачи директории вместо файла
        with pytest.raises(ValueError):
            read_csv(tmp_path)

    def test_parse_filter_valid(self):
        # Тест парсинга фильтра
        col, op, value = parse_filter('price>100')
        assert col == 'price'
        assert op == '>'
        assert value == '100'

    def test_parse_filter_invalid(self):
        # Тест невалидного фильтра
        with pytest.raises(ValueError):
            parse_filter('price_100')

    def test_apply_filter_numeric(self):
        # Тест числовой фильтрации
        data = read_csv(self.csv_path)
        filtered = apply_filter(data, 'price', '>', '70')
        assert len(filtered) == 3
        assert filtered[0]['product'] == 'Apple'
        assert filtered[1]['product'] == 'Orange'
        assert filtered[2]['product'] == 'Milk'

    def test_apply_filter_string(self):
        # Тест строковой фильтрации
        data = read_csv(self.csv_path)
        filtered = apply_filter(data, 'product', '=', 'Banana')
        assert len(filtered) == 1
        assert filtered[0]['product'] == 'Banana'

    def test_apply_filter_missing_column(self):
        # Тест отсутствующей колонки
        data = read_csv(self.csv_path)
        with pytest.raises(ValueError):
            apply_filter(data, 'color', '=', 'red')

    def test_parse_agg_valid(self):
        # Тест парсинга агрегации
        func, col = parse_agg('avg(price)')
        assert func == 'avg'
        assert col == 'price'

    def test_parse_agg_invalid(self):
        # Тест невалидной агрегации
        with pytest.raises(ValueError):
            parse_agg('avg(price')

    def test_apply_agg_avg(self):
        # Тест среднего значения
        data = read_csv(self.csv_path)
        result = apply_agg(data, 'price', 'avg')
        assert result == pytest.approx(86.25, 0.01)

    def test_apply_agg_min(self):
        # Тест минимального значения
        data = read_csv(self.csv_path)
        result = apply_agg(data, 'price', 'min')
        assert result == 50

    def test_apply_agg_max(self):
        # Тест максимального значения
        data = read_csv(self.csv_path)
        result = apply_agg(data, 'price', 'max')
        assert result == 120

    def test_apply_agg_missing_column(self):
        # Тест отсутствующей колонки
        data = read_csv(self.csv_path)
        with pytest.raises(ValueError):
            apply_agg(data, 'color', 'avg')

    def test_apply_agg_non_numeric(self):
        # Тест нечисловых значений
        data = read_csv(self.csv_path)
        with pytest.raises(ValueError):
            apply_agg(data, 'product', 'avg')

    def test_main_full_flow(self, capsys, monkeypatch):
        # Тест полного потока с агрегацией
        monkeypatch.setattr('sys.argv',
                            ['main.py', '--file', self.csv_path, '--where', 'price>70', '--aggregate', 'avg(stock)'])
        main()
        captured = capsys.readouterr()
        assert "avg(stock)" in captured.out
        assert "51.67" in captured.out

    def test_main_without_agg(self, capsys, monkeypatch):
        # Тест вывода таблицы
        monkeypatch.setattr('sys.argv', ['main.py', '--file', self.csv_path])
        main()
        captured = capsys.readouterr()
        assert "product" in captured.out
        assert "price" in captured.out
        assert "stock" in captured.out
        assert "Apple" in captured.out

    def test_main_file_error(self, capsys, monkeypatch):
        # Тест обработки ошибки файла
        monkeypatch.setattr('sys.argv', ['main.py', '--file', 'invalid.csv'])
        main()
        captured = capsys.readouterr()
        assert "Ошибка: Файл не найден" in captured.out

    def test_main_filter_error(self, capsys, monkeypatch):
        # Тест ошибки фильтрации
        monkeypatch.setattr('sys.argv', ['main.py', '--file', self.csv_path, '--where', 'invalid>100'])
        main()
        captured = capsys.readouterr()
        assert "Ошибка фильтрации" in captured.out

    def test_main_agg_error(self, capsys, monkeypatch):
        # Тест ошибки агрегации
        monkeypatch.setattr('sys.argv', ['main.py', '--file', self.csv_path, '--aggregate', 'sum(price)'])
        main()
        captured = capsys.readouterr()
        assert "Ошибка агрегации" in captured.out