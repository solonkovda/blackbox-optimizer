# Black-box optimizer
Данный сервис представляет из себя реализацию "Black-box optimization as a Service". Он разделен на две основные
компоненты:

* Сервер - обеспечивает клиентское взаимодействие и раздает задания вычислительным узлам
* Вычислительный узел - получает задания от сервера и выполняет оптимизации и вычисление black-box функций. 
## Требования
Для сборки сервиса требуется установить [Bazel](https://docs.bazel.build/versions/master/install-ubuntu.html)

Для запуска серверной части сервиса требуется настроить PostgreSQL базу данных и предоставить серверу доступ к ней.
## Как запустить
### Сервер
```bash
export DATA_FOLDER=/path/to/folder
export DATABASE_HOST=<address to your database>
export DATABASE_USER=<database user name>
export DATABASE_PASSWORD=<database user password>
export DATABASE_NAME=<name of the database>

bazel run //server:blackbox_server
```
Где `/path/to/folder` - путь к папке, в которой сервер будет хранить свои метаданные.
### Вычислительный узел
```bash
export DATA_FOLDER=/path/to/folder
export SERVER_ADDRESS=<server address>
```
Где `/path/to/folder/` - путь к папке, в которой узел будет хранить свои метаданные, а `<server address>` - адрес
сервера, поднятого на прошлом шагу.
## Тестирование
К сервису прилагается набор базовых функций, которые могут быть использованы для тестирования, находящие в папке `examples`:
* `sin_1d.py` - функция от одной переменной, вычисляющая sin(x)
* `rosenbrock_2d.py` - [Функция Розенброка](https://en.wikipedia.org/wiki/Rosenbrock_function) от двух переменных
* `rock_paper_scissors.py` - пример использования категориальных переменных.

Чтобы запустить все эти примеры на сервере и посмотреть на результат их работы необходимо запустить сервер, хотя бы один
 вычислительный узел и выполнить
следующую команду:
```bash
bazel run //examples:run_examples --address <server address>
```
Для дополнительных опций запуска тестирования смотрите:
```bash
bazel run //examples:run_examples --help
```
