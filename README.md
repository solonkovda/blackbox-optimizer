# Прототип
## Требования
Для сборки прототипа требуется установить [Bazel](https://docs.bazel.build/versions/master/install-ubuntu.html)
## Сборка и запуск сервера
```bash
git clone git@github.com:solonkovda/blackbox-optimizer.git
cd blackbox-optimizer
git checkout prototype
export BLACKBOX_DATA_FOLDER=/path/to/folder
bazel run //prototype/server:blackbox_server
```
Где `/path/to/folder` - путь к папке, в которой сервер будет хранить свои метаданные.

## Тестирование
К протитипу прилагаются 3 базовых примера, находящие в папке `prototype/examples`:
* `sin_1d.py` - функция от одной переменной, вычисляющая sin(x)
* `rosenbrock_2d.py` - [Функция Розенброка](https://en.wikipedia.org/wiki/Rosenbrock_function) от двух переменных
* `calculator.py` - пример категориальных переменных, применяет переданную операцию с переменными `x` и `y`.

Чтобы запустить все эти примеры на сервере и посмотреть на результат их работы необходимо запустить сервер и выполнить
следующую команду:
```bash
bazel run //prototype/examples:run_examples
```
