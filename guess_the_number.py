# Курсовая работа: консольная игра «Угадай число».
# Режимы: пользователь угадывает число компьютера (с подсказками
# «горячо/холодно») и компьютер угадывает число пользователя методом
# половинного деления. Есть уровни сложности, очки, статистика сессии
# и самотестирование.

from random import randint

# Маски битовых флагов: какие режимы уже были сыграны в этой сессии.
FLAG_PLAYED_USER = 1 << 0
FLAG_PLAYED_COMPUTER = 1 << 1

# Состояние сессии (меняется функциями update_stats_* через global).
played_flags = 0
count_plays_user = 0
count_win_user = 0
count_attempts_user = 0
user_points = 0
count_plays_computer = 0
count_attempts_computer = 0

# Счётчики самотестирования.
tests_run = 0
tests_passed = 0


# ---------------------------------------------------------------------------
# Вывод на экран
# ---------------------------------------------------------------------------

# Назначение: приветствие при запуске программы.
# Параметры: нет.
# Результат: нет (печатает текст).
def print_hello():
    print(
        "Добро пожаловать в игру - Угадай число!\n"
        "Чтобы продолжить, введите число от 0 до 4."
    )


# Назначение: вывод главного меню.
# Параметры: нет.
# Результат: нет (печатает текст).
def print_menu():
    print(
        "Меню:\n"
        "\t1. Угадать\n"
        "\t2. Загадать\n"
        "\t3. Статистика\n"
        "\t4. Тесты\n"
        "\t0. Выход\n"
    )


# Назначение: вывод списка уровней сложности.
# Параметры: нет.
# Результат: нет (печатает текст).
def print_levels():
    print(
        "Уровни:\n"
        "\t1. [1, 10]\n"
        "\t2. [1, 100]\n"
        "\t3. [1, 1000]\n"
        "\t0. Назад\n"
    )


# Назначение: сообщение о неверном вводе.
# Параметры: нет.
# Результат: нет (печатает текст).
def print_error():
    print("\nОшибка! Повторите попытку\n")


# Назначение: правила режима «Загадать» (угадывает компьютер).
# Параметры: range_size - верхняя граница диапазона.
# Результат: нет (печатает текст).
def print_computer_rules(range_size):
    print(
        f"Загадайте число от 1 до {range_size} и введите его: оно нужно "
        "только для проверки ваших подсказок.\n"
        "Компьютер будет называть числа, отвечайте:\n"
        "\t>  - ваше число больше названного\n"
        "\t<  - ваше число меньше названного\n"
        "\t+  - компьютер угадал\n"
    )


# ---------------------------------------------------------------------------
# Ввод и проверка данных
# ---------------------------------------------------------------------------

# Назначение: проверить, что строка - неотрицательное целое число.
# Параметры: text - введённая строка.
# Результат: True, если строка непустая и состоит только из цифр.
def is_valid_num(text):
    if text == "":
        return False
    valid_digits = "0123456789"
    for symbol in text:
        if symbol not in valid_digits:
            return False
    return True


# Назначение: прочитать целое число, повторяя запрос при ошибке.
# Параметры: prompt - приглашение к вводу.
# Результат: введённое целое число.
def read_int(prompt="Введите число: "):
    while True:
        text = input(prompt)
        if is_valid_num(text):
            return int(text)
        print_error()


# Назначение: прочитать целое число из заданного отрезка.
# Параметры: low, high - границы отрезка; prompt - приглашение к вводу.
# Результат: число, для которого low <= число <= high.
def read_in_range(low, high, prompt="Введите число: "):
    while True:
        number = read_int(prompt)
        if low <= number <= high:
            return number
        print_error()


# Назначение: прочитать подсказку пользователя для компьютера.
# Параметры: нет.
# Результат: одна из строк ">", "<", "+".
def read_hint_answer():
    while True:
        answer = input("Ваш ответ (>, <, +): ")
        if answer == ">" or answer == "<" or answer == "+":
            return answer
        print_error()


# Назначение: выбор уровня сложности.
# Параметры: нет.
# Результат: номер уровня 1-3 или 0, если пользователь вернулся назад.
def choose_level():
    print_levels()
    return read_in_range(0, 3)


# ---------------------------------------------------------------------------
# Логика игры
# ---------------------------------------------------------------------------

# Назначение: размер диапазона для уровня: 10, 100, 1000.
# Параметры: level - номер уровня (1-3).
# Результат: верхняя граница диапазона [1, N].
def get_range_size(level):
    return 10 ** level


# Назначение: число попыток для уровня. Значения 4, 7, 10 не меньше
# log2 от размера диапазона, поэтому число всегда можно угадать.
# Параметры: level - номер уровня (1-3).
# Результат: максимальное число попыток.
def get_max_attempts(level):
    return 3 * level + 1


# Назначение: создать функцию-подсказку «горячо/тепло/холодно»
# (замыкание: пороги зависят от размера диапазона).
# Параметры: range_size - размер диапазона;
#            distance - функция расстояния между двумя числами.
# Результат: функция hint(guess, secret), возвращающая строку подсказки.
def make_hint_strategy(range_size, distance):
    hot = range_size // 10
    warm = range_size // 4

    def hint(guess, secret):
        d = distance(guess, secret)
        if d <= hot:
            return "Горячо!"
        elif d <= warm:
            return "Тепло."
        return "Холодно!"

    return hint


# Назначение: подсчёт очков за игру. Чем раньше угадано и чем выше
# уровень, тем больше очков.
# Параметры: win - выиграна ли игра (True/False);
#            attempts - потрачено попыток; max_attempts - всего попыток;
#            level - номер уровня.
# Результат: очки (0 при проигрыше).
def calc_score(win, attempts, max_attempts, level):
    if not win:
        return 0
    return (max_attempts - attempts + 1) * 10 * level


# Назначение: среднее значение (безопасное деление).
# Параметры: total - сумма; count - количество.
# Результат: total / count или 0, если count равен 0.
def calc_average(total, count):
    if count == 0:
        return 0
    return total / count


# Назначение: композиция двух функций.
# Параметры: f, g - функции одного аргумента.
# Результат: функция composed(x), равная f(g(x)).
def compose(f, g):
    def composed(x):
        return f(g(x))

    return composed


# Назначение: установить флаг (побитовое ИЛИ).
# Параметры: flags - текущие флаги; mask - маска устанавливаемого бита.
# Результат: флаги с установленным битом.
def set_flag(flags, mask):
    return flags | mask


# Назначение: проверить флаг (побитовое И).
# Параметры: flags - текущие флаги; mask - маска проверяемого бита.
# Результат: True, если бит установлен.
def has_flag(flags, mask):
    return (flags & mask) != 0


# ---------------------------------------------------------------------------
# Раунды
# ---------------------------------------------------------------------------

# Назначение: один раунд, в котором угадывает пользователь.
# Параметры: secret - загаданное число; max_attempts - число попыток;
#            range_size - размер диапазона;
#            hint_func - функция подсказки hint(guess, secret).
# Результат: номер удачной попытки или 0, если число не угадано.
def play_round(secret, max_attempts, range_size, hint_func):
    for attempt in range(1, max_attempts + 1):
        print(f"Попытка №{attempt} из {max_attempts}.")
        guess = read_in_range(1, range_size)
        if guess == secret:
            return attempt
        print(hint_func(guess, secret))
    return 0


# Назначение: один раунд, в котором угадывает компьютер
# (половинное деление с проверкой подсказок по секрету).
# Параметры: secret - число пользователя; range_size - размер диапазона;
#            choose_mid - функция выбора середины choose_mid(low, high).
# Результат: число попыток или 0, если подсказки противоречат числу.
def computer_round(secret, range_size, choose_mid):
    low = 1
    high = range_size
    attempts = 0
    while low <= high:
        attempts += 1
        mid = choose_mid(low, high)
        print(f"Попытка №{attempts}. Ваше число - {mid}?")
        answer = read_hint_answer()
        if answer == "+" and secret == mid:
            return attempts
        elif answer == ">" and secret > mid:
            low = mid + 1
        elif answer == "<" and secret < mid:
            high = mid - 1
        else:
            print("Ваша подсказка не сходится с загаданным числом!")
            return 0
    return 0


# ---------------------------------------------------------------------------
# Статистика
# ---------------------------------------------------------------------------

# Назначение: учесть сыгранную игру пользователя в статистике.
# Параметры: win - выиграна ли игра; attempts - потрачено попыток;
#            points - полученные очки.
# Результат: нет (меняет глобальные счётчики).
def update_stats_play(win, attempts, points):
    global played_flags, count_plays_user, count_win_user
    global count_attempts_user, user_points
    played_flags = set_flag(played_flags, FLAG_PLAYED_USER)
    count_plays_user += 1
    if win:
        count_win_user += 1
    count_attempts_user += attempts
    user_points += points


# Назначение: учесть игру компьютера в статистике.
# Параметры: attempts - потрачено попыток.
# Результат: нет (меняет глобальные счётчики).
def update_stats_computer(attempts):
    global played_flags, count_plays_computer, count_attempts_computer
    played_flags = set_flag(played_flags, FLAG_PLAYED_COMPUTER)
    count_plays_computer += 1
    count_attempts_computer += attempts


# ---------------------------------------------------------------------------
# Обработчики пунктов меню
# ---------------------------------------------------------------------------

# Назначение: пункт «Угадать» - пользователь угадывает число.
# Параметры: нет.
# Результат: нет (играет раунд и обновляет статистику).
def handle_play():
    level = choose_level()
    if level == 0:
        return
    range_size = get_range_size(level)
    max_attempts = get_max_attempts(level)
    hint_func = make_hint_strategy(range_size, lambda a, b: abs(a - b))
    secret = randint(1, range_size)
    print(f"Я загадал число от 1 до {range_size}. Попыток: {max_attempts}.")

    result = play_round(secret, max_attempts, range_size, hint_func)
    win = result != 0
    attempts = result if win else max_attempts
    if win:
        print(f"Вы выиграли! Загаданное число - {secret}!")
    else:
        print(f"Вы проиграли! Загаданное число - {secret}.")

    points = calc_score(win, attempts, max_attempts, level)
    print(f"Очки за игру: {points}")
    update_stats_play(win, attempts, points)


# Назначение: пункт «Загадать» - число угадывает компьютер.
# Параметры: нет.
# Результат: нет (играет раунд и обновляет статистику).
def handle_computer():
    level = choose_level()
    if level == 0:
        return
    range_size = get_range_size(level)
    print_computer_rules(range_size)
    secret = read_in_range(1, range_size, "Ваше число: ")

    attempts = computer_round(
        secret, range_size, lambda low, high: (low + high) // 2
    )
    if attempts == 0:
        print("Раунд прерван и в статистику не попадёт.")
    else:
        print(f"Компьютер угадал число {secret} за {attempts} попыток!")
        update_stats_computer(attempts)


# Назначение: пункт «Статистика» - вывод итогов сессии.
# Параметры: нет.
# Результат: нет (печатает статистику).
def handle_stats():
    format_percent = compose(lambda text: text + " %", str)
    format_average = compose(str, lambda number: round(number, 2))

    print("Статистика сессии:")
    print("Пользователь (режим «Угадать»):")
    if has_flag(played_flags, FLAG_PLAYED_USER):
        win_percent = count_win_user * 100 // count_plays_user
        average = calc_average(count_attempts_user, count_plays_user)
        print(f"\tИгр: {count_plays_user}")
        print(f"\tПобед: {count_win_user}")
        print(f"\tПоражений: {count_plays_user - count_win_user}")
        print(f"\tПроцент побед: {format_percent(win_percent)}")
        print(f"\tОчков: {user_points}")
        print(f"\tСреднее число попыток: {format_average(average)}")
    else:
        print("\tЕщё нет игр.")

    print("Компьютер (режим «Загадать»):")
    if has_flag(played_flags, FLAG_PLAYED_COMPUTER):
        average = calc_average(count_attempts_computer, count_plays_computer)
        print(f"\tИгр: {count_plays_computer}")
        print(f"\tСреднее число попыток: {format_average(average)}")
    else:
        print("\tЕщё нет игр.")


# ---------------------------------------------------------------------------
# Самотестирование
# ---------------------------------------------------------------------------

# Назначение: выполнить один тест и вывести «OK» или «FAIL».
# Параметры: func - проверяемая функция; expected - ожидаемый результат;
#            *args - аргументы для вызова func.
# Результат: нет (печатает итог и меняет счётчики тестов).
def check(func, expected, *args):
    global tests_run, tests_passed
    tests_run += 1
    result = func(*args)
    if result == expected:
        tests_passed += 1
        print(f"Тест {tests_run}: OK")
    else:
        print(
            f"Тест {tests_run}: FAIL "
            f"(ожидалось {expected}, получено {result})"
        )


# Назначение: пункт «Тесты» - запуск всех проверок.
# Параметры: нет.
# Результат: нет (печатает результаты и итог).
def handle_tests():
    global tests_run, tests_passed
    tests_run = 0
    tests_passed = 0
    hint = make_hint_strategy(100, lambda a, b: abs(a - b))

    print("Самотестирование:")
    check(is_valid_num, True, "2026")
    check(is_valid_num, False, "")
    check(is_valid_num, False, "12a")
    check(get_range_size, 100, 2)
    check(get_range_size, 1000, 3)
    check(get_max_attempts, 4, 1)
    check(get_max_attempts, 10, 3)
    check(calc_score, 300, True, 1, 10, 3)
    check(calc_score, 10, True, 10, 10, 1)
    check(calc_score, 0, False, 10, 10, 2)
    check(calc_average, 2.5, 10, 4)
    check(calc_average, 0, 5, 0)
    check(hint, "Горячо!", 50, 55)
    check(hint, "Тепло.", 50, 70)
    check(hint, "Холодно!", 50, 95)
    check(compose(lambda x: x + 1, lambda x: x * 2), 11, 5)
    check(set_flag, 2, 0, FLAG_PLAYED_COMPUTER)
    check(has_flag, True, 3, FLAG_PLAYED_USER)
    check(has_flag, False, 2, FLAG_PLAYED_USER)
    print(f"Пройдено {tests_passed} из {tests_run}.")


# ---------------------------------------------------------------------------
# Главный цикл
# ---------------------------------------------------------------------------

# Назначение: главный цикл программы с меню; выход - пункт 0.
# Параметры: нет.
# Результат: нет.
def main():
    print_hello()
    while True:
        print_menu()
        item = read_in_range(0, 4)
        if item == 1:
            handle_play()
        elif item == 2:
            handle_computer()
        elif item == 3:
            handle_stats()
        elif item == 4:
            handle_tests()
        else:
            print("До свидания!")
            break


main()
