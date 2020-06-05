# Black-box optimizer
Данный сервис представляет из себя реализацию "Black-box optimization as a Service". Он разделен на две основные
компоненты:

* Сервер - обеспечивает клиентское взаимодействие и раздает задания вычислительным узлам
* Вычислительный узел - получает задания от сервера и выполняет оптимизации и вычисление black-box функций. 
## Руководство по сборке и запуску
### Использование готовых docker images
Для этого способа необходим [Docker](https://www.docker.com/) и [docker-compose](https://docs.docker.com/compose/).

Сначала необходимо склонировать репозиторий.
```bash
git clone git@github.com:solonkovda/blackbox-optimizer.git
cd blackbox-optimizer
```

Задание следующих переменных окружения перед запуском сервера позволяет конфигурировать его:
* `GARBAGE_WAIT_TIME` - время (в секундах) между запусками сборки мусора
* `CLIENT_ACTIVE_TIME` - время (в секундах) отсутствия сердцебиения от вычислительного узла после которого он признается
отказавшим

Запуск:
```bash
docker-compose -f docker-compose-server.yml pull
docker-compose -f docker-compose-server.yml up -d
```
Остановка:
```bash
docker-compose -f docker-compose-server.yml down
```
Логи работающего сервера
```bash
docker-compose -f docker-compose-server.yml logs
```
#### Вычислительный узел
Для запуска необходимо задать переменную окружения `SERVER_ADDRESS`, указывающую на адрес сервера.
Если запуск узла проходит с той же машины, что и сервер, то `localhost:50051` является рабочим адресом. Дополнительно, 
вычислительный узел поддерживает следующие переменные окружения:
* `HEARTBEAT_TIME` - время (в секундах) между отправками сердцебиения на сервер
* `RESPONSE_DELAY` - время (в секундах) между запросами новых заданий у сервера.
* `MAX_WORKERS` - максимальное число процессов выполнения заданий, которое может быть одновременно запущено на
вычислительном узле.
* `MAX_JOBS_PER_ACTIVE_WORKER` - запущенный процесс оптимизации будет создавать не более, чем это число запросов
вычисления на каждый активный вычислительный узел в системе.
* `LOG_LEVEL`. Установка этой переменной в `DEBUG` покажет дебаг информацию. 

Запуск:
```bash
docker-compose -f docker-compose-worker.yml pull
export SERVER_ADDRESS=<address>
docker-compose -f docker-compose-worker.yml up -d
```
Остановка:
```bash
docker-compose -f docker-compose-worker.yml down
```
Логи работающего узла:
```bash
docker-compose -f docker-compose-worker.yml logs
```
## Запуск из исходного кода
Для запуска из исходного кода потребуется [Bazel](https://bazel.build/) и поднятая
[PostgreSQL](https://www.postgresql.org/) база данных на сервере.
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

bazel run //worker:worker_client
```
Где `/path/to/folder/` - путь к папке, в которой узел будет хранить свои метаданные, а `<server address>` - адрес
сервера, поднятого на прошлом шагу.
## Тестирование
К сервису прилагается набор базовых функций, которые могут быть использованы для тестирования, находящие в папке 
`examples`:
* `finding_discrete_point.py` - пример использования дискретных переменных. Задача представляет из себя поиск точки на
дискретной координатной сетке.
* `rock_paper_scissors.py` - пример использования категориальных переменных. Задача представляет из себя поиск
проигрышной пары ходов в камень-ножницы-бумага.
* `rosenbrock_2d.py` - [Функция Розенброка](https://en.wikipedia.org/wiki/Rosenbrock_function) от двух переменных
* `simple_4_variable_knapsack.py` - Простой пример [задачи о рюкзаке](https://en.wikipedia.org/wiki/Knapsack_problem).
Используется как демонстрация системы ограничений, позволяющая ограничить допустимое множество точек, доступное задаче. 
* `sin_1d.py` - функция от одной переменной, вычисляющая sin(x)
* `sin_1d_argument.py` - аналогично `sin_1d.py`. Демонстрирует передачу переменных в виде аргументов командной строки
* `sin_1d_environment.py` - аналогично `sin_1d.py`. Демонстрирует передачу переменных в виде переменных окружения.

Чтобы запустить все эти примеры на сервере и посмотреть на результат их работы необходимо запустить сервер, хотя бы один
 вычислительный узел и выполнить
следующую команду:
```bash
bazel run //examples:run_examples --address <server address>
```
Для дополнительных опций запуска тестирования(ограничения времени работы, алгоритма оптимизации и прочего) смотрите:
```bash
bazel run //examples:run_examples --help
```
