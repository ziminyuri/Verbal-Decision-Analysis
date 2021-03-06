import datetime
from collections import deque

from django.db.models import Max

from model.models import Criterion, Model, Option, Value
from pacom.models import (HistoryAnswerPACOM, PairsOfOptionsPARK,
                          PerfectAlternativePARK, RangeValue,
                          ValueOfPerfectAlternativePARK)
from services.normalisation import normalisation_time
from services.pairs_of_options import _replace_line_file, _write_file
from services.range_value import create_range_value
from services.request import request as request_obj
from VDA.settings import MEDIA_ROOT


def get_park_question(model):
    try:
        # Пары для сравнения существуют
        pair = PairsOfOptionsPARK.objects.filter(id_model=model).filter(already_find_winner=False). \
            filter(already_range=True).first()
    except Exception as e:
        print(e)

    if not pair:
        try:
            pair = PairsOfOptionsPARK.objects.filter(id_model=model).filter(already_find_winner=False). \
                filter(already_range=False).first()

            if pair:
                data, option_1, option_2 = _get_range_data(model, pair)
                _add_1_to_number_of_question(model)
                return {'flag_find_winner': False, 'flag_range': False, 'flag_compare': False, 'pair': pair.id,
                        'option_1': option_1, 'option_2': option_2, 'data': data}
            else:
                pair = PairsOfOptionsPARK.objects.filter(id_model=model)

                if not pair:
                    # Впервые пришли к сранению -> Пар сравнения нет
                    # Процесс подготовки данных для ранжирования

                    pair = _create_pair(model, FIRST=True)
                    data, option_1, option_2 = _get_range_data(model, pair)

                    _create_perfect_fit(pair, model)  # Создаем идеальный вариант в паре (лучшие значения по критериям)

                    Model.objects.filter(id=model.id).update(time_answer_pacom=str(datetime.datetime.now()))
                    _add_1_to_number_of_question(model)
                    return {'flag_find_winner': 0, 'flag_range': False, 'flag_compare': False, 'pair': pair.id,
                            'option_1': option_1,
                            'option_2': option_2, 'data': data}
                else:
                    quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_pacom'))[
                        'quasi_order_pacom__max']
                    options_with_quasi_max_order = Option.objects.filter(quasi_order_pacom=quasi_max_order, id_model=model)
                    options_with_quasi_0 = Option.objects.filter(quasi_order_pacom=-1, id_model=model).first()

                    if options_with_quasi_0:
                        # Пока есть альтернативы с квазипорядком равным -1
                        for option in options_with_quasi_max_order:
                            pair = _create_pair(model, quasi_max_order=quasi_max_order, option_1=option, option_2=options_with_quasi_0)

                            """Создаем идеальный вариант"""
                            _create_perfect_fit(pair, model)

                        data, option_1, option_2 = _get_range_data(model, pair)
                        _add_1_to_number_of_question(model)
                        return {'flag_find_winner': False, 'flag_range': False, 'flag_compare': False, 'pair': pair.id,
                                'option_1': option_1, 'option_2': option_2, 'data': data}
                    else:
                        # Нашли победителей
                        print('Нашли победителей')
                        Model.objects.filter(id=model.id).update(quasi_max_order_pacom=quasi_max_order)
                        fix_quasi_order_pacom(model.id)
                        update_model_after_find_winner(model)
                        return get_winners_from_model(model)
        except Exception as e:
            print(e)

    try:
        if pair.init_file is False:
            try:
                # Подготавливаем данные для первого сравнения
                _init_file_for_PARK(model, pair)
            except Exception as e:
                print(e)
                print(10)

        else:
            try:
                # Данные в файл для второго сравнения
                winner_find = _fill_file_alternative(model, pair)
                if winner_find:
                    response = get_park_question(model)
                    return response
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)

    try:
        perfect_alternative = PerfectAlternativePARK.objects.get(pair=pair)
        criterions = Criterion.objects.filter(id_model=model.id)

        new_alternative_1, new_alternative_2 = _fill_new_alternative(criterions, perfect_alternative, pair)
        _add_1_to_number_of_question(model)
        return {'flag_range': True, 'alternative_1': new_alternative_1, 'alternative_2': new_alternative_2,
                'criterions': criterions, 'pair': pair.id, 'flag_find_winner': False, 'name_1': pair.id_option_1.name,
                'name_2': pair.id_option_2.name}

    except Exception as e:
        print(e)


# Записываем данные о ранжировании критериев в паре
def write_range_data(response, model, auto_mode=False) -> object:
    criterions = Criterion.objects.filter(id_model=model.id)

    if auto_mode:
        pair_id = int(response["pair"])
    else:
        pair_id = int(response.POST["pair"])

    pair: object = PairsOfOptionsPARK.objects.get(id=pair_id)

    range_value_1 = False
    range_value_2 = False

    for criterion in criterions:
        try:
            value_name = f'value_{str(criterion.id)}_1'

            if auto_mode:
                value = int(response[value_name])
            else:
                value = int(response.POST[value_name])

            create_range_value(pair, pair.id_option_1, criterion, value)
            range_value_1 = True
        except:
            try:
                value_name = f'value_{str(criterion.id)}_2'

                if auto_mode:
                    value = int(response[value_name])
                else:
                    value = int(response.POST[value_name])

                create_range_value(pair, pair.id_option_2, criterion, value)
                range_value_2 = True
            except:
                pass

    if not range_value_1 and not range_value_2:
        _find_winner_in_pair(pair, result=0)
    elif not range_value_1:
        _find_winner_in_pair(pair, result=1)
    elif not range_value_2:
        _find_winner_in_pair(pair, result=2)

    PairsOfOptionsPARK.objects.filter(id=pair_id).update(already_range=True)


def write_result_of_compare_pacom(response, model, auto_mode=False):
    """# Записываем результаты сравнения парной компенсации"""
    try:
        if auto_mode:
            pair_id = int(response["pair"])
            answer = int(response["answer"])
        else:
            pair_id = int(response.POST["pair"])
            answer = int(response.POST["answer"])
    except Exception as e:
        print(e)
        print(14)

    try:
        try:
            pair: object = PairsOfOptionsPARK.objects.get(id=pair_id)

            if pair.compensable_option is None:
                # Не найдена компенсируемая альтернатива

                if answer == 1:
                    PairsOfOptionsPARK.objects.filter(id=pair_id).update(compensable_option=pair.id_option_2)
                elif answer == 2:
                    PairsOfOptionsPARK.objects.filter(id=pair.id).update(compensable_option=pair.id_option_1)

            if answer == 3:
                _update_pair_to_not_comparable(pair)
        except Exception as e:
            print(e)

        try:
            path_dir = f'{MEDIA_ROOT}/files/models/{str(model.id)}/pacom/'
            path = f'{path_dir}PAIR{str(pair.id)}.txt'
            last_line = _get_last_line(path)
            new_line = f'{last_line}={str(answer)}\n'
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)
        print(15)

    try:
        try:
            _replace_line_file(new_line, last_line, path)
        except Exception as e:
            print(e)

        try:
            _write_history(pair, model, last_line, answer)
        except Exception as e:
            print(e)

    except Exception as e:
        print(e)
        print(15)


def _create_pair(model, quasi_max_order=None, FIRST=False, option_1=None, option_2=None):
    if FIRST:
        options = Option.objects.filter(id_model=model)
        pair = PairsOfOptionsPARK.objects.create(id_option_1=options[0], id_option_2=options[1], id_model=model,
                                                 quasi_level=1)
        return pair

    else:
        pair = PairsOfOptionsPARK.objects.create(id_option_1=option_1, id_option_2=option_2, id_model=model,
                                                 quasi_level=quasi_max_order + 1)
        return pair


# Возвращает данные для ранжирования: 2 модели и значения критериев
def _get_range_data(model, pair):
    data = []
    criterions = Criterion.objects.filter(id_model=model.id)
    for criterion in criterions:
        id_option_1 = pair.id_option_1
        id_option_2 = pair.id_option_2

        value_2 = Value.objects.filter(id_option=id_option_2, id_criterion=criterion).first()
        value_1 = Value.objects.filter(id_option=id_option_1, id_criterion=criterion).first()

        line = {'criterion': criterion.name, 'criterion_id': criterion.id, 'direction': criterion.direction,
                'pair': pair.id,
                'option_1': value_1.value, 'option_2': value_2.value}
        data.append(line)

    return data, pair.id_option_1.name, pair.id_option_2.name


# Создаем идеальную альтернативу в паре: лучшие значения критериев в паре
def _create_perfect_fit(pair: object, model: object) -> None:
    try:
        perfect_alternative = PerfectAlternativePARK.objects.create(pair=pair)
        criterions = Criterion.objects.filter(id_model=model.id)
        for criterion in criterions:
            value_1 = Value.objects.get(id_option=pair.id_option_1, id_criterion=criterion)
            value_2 = Value.objects.get(id_option=pair.id_option_2, id_criterion=criterion)

            # Направление -> max
            if criterion.direction is True:
                if value_1.value > value_2.value:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_1.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative,
                                                                 name=value_1.name)
                else:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_2.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative,
                                                                 name=value_2.name)
            # Направление -> min
            else:
                if value_1.value < value_2.value:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_1.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative,
                                                                 name=value_1.name)
                else:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_2.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative,
                                                                 name=value_2.name)

    except Exception as e: pass


# Создаем историю ответов для пары альтернатив
def _init_file_for_PARK(model: object, pair: object) -> None:
    import os
    try:
        range_1 = RangeValue.objects.filter(pair=pair).filter(option=pair.id_option_1).filter(value=1).first()
        range_2 = RangeValue.objects.filter(pair=pair).filter(option=pair.id_option_2).filter(value=1).first()

        value_1 = Value.objects.filter(id_option=pair.id_option_1).filter(id_criterion=range_1.criteria).first()
        value_2 = Value.objects.filter(id_option=pair.id_option_2).filter(id_criterion=range_2.criteria).first()

    except Exception as e:
        print(e)
    path_dir = f'{MEDIA_ROOT}/files/models/{str(model.id)}'
    try:
        os.mkdir(path_dir)
    except:
        pass

    path_dir = f'{MEDIA_ROOT}/files/models/{str(model.id)}/pacom/'
    try:
        os.mkdir(path_dir)
    except Exception as e:
        pass

    path = f'{path_dir}PAIR{str(pair.id)}.txt'
    line = f'{str(value_1.id_criterion.number)}|{str(value_2.id_criterion.number)}'
    _write_file(line, path)
    PairsOfOptionsPARK.objects.filter(id=pair.id).update(init_file=True)


# Заполняем файл НЕ для первого сравнения
def _fill_file_alternative(model, pair):
    path = f'{MEDIA_ROOT}/files/models/{str(pair.id_model.id)}/pacom/PAIR{str(pair.id)}.txt'
    last_line = _get_last_line(path)

    set_1_line = last_line.split('|')[0]
    set_2_line = last_line.split('|')[1].split('=')[0]
    result = int(last_line.split('|')[1].split('=')[1])
    set_1 = set_1_line.split(';')
    set_2 = set_2_line.split(';')

    if pair.compensable_option == pair.id_option_1:
        id_compensable_option = 1
    else:
        id_compensable_option = 2

    criterion_1 = Criterion.objects.get(id_model=model, number=set_1[-1])
    criterion_2 = Criterion.objects.get(id_model=model, number=set_2[-1])

    range_obj_next_1 = None
    range_obj_next_2 = None

    if result == 0 or result == 1 or (result == 2 and id_compensable_option == 2):
        range_obj_old_1 = RangeValue.objects.filter(pair=pair, option=pair.id_option_1, criteria=criterion_1).first()
        range_obj_next_1 = RangeValue.objects.filter(pair=pair, option=pair.id_option_1, value=range_obj_old_1.value + 1).first()

    if result == 0 or result == 2 or (result == 1 and id_compensable_option == 1):
        range_obj_old_2 = RangeValue.objects.filter(pair=pair, option=pair.id_option_2, criteria=criterion_2).first()
        range_obj_next_2 = RangeValue.objects.filter(pair=pair, option=pair.id_option_2, value=range_obj_old_2.value + 1).first()

    if (range_obj_next_1 is not None) and (range_obj_next_2 is not None):
        line = f'{str(range_obj_next_1.criteria.number)}|{str(range_obj_next_2.criteria.number)}'
        _write_file(line, path)

    elif result == 1 and (range_obj_next_1 is not None):
        set_1.append(range_obj_next_1.criteria.number)
        new_line = _fill_line_from_list(set_1)
        line = f'{new_line}|{set_2_line}'
        _write_file(line, path)

    elif result == 2 and (range_obj_next_2 is not None):
        set_2.append(range_obj_next_2.criteria.number)
        new_line = _fill_line_from_list(set_2)
        line = f'{set_1_line}|{new_line}'
        _write_file(line, path)

    else:
        if range_obj_next_2 is None:
            _find_winner_in_pair(pair,  option_2_is_empty=True)
        elif range_obj_next_1 is None:
            _find_winner_in_pair(pair, option_1_is_empty=True)
        else:
            _find_winner_in_pair(pair)
        return True

    return False


# Заполняем новые варианты
def _fill_new_alternative(criterions: list, perfect_alternative: object, pair: object):
    larichev_question = pair.id_model.id_settings_pacom.larichev_question
    new_alternative_1 = []
    new_alternative_2 = []

    path = f'{MEDIA_ROOT}/files/models/{str(pair.id_model.id)}/pacom/PAIR{str(pair.id)}.txt'
    with open(path) as file:
        [last_line] = deque(file, maxlen=1) or ['']

    set_1 = last_line.split('|')[0]
    set_2 = last_line.split('|')[1].split('=')[0]
    set_1 = set_1.split(';')
    set_2 = set_2.split(';')

    iter = 1
    for criterion in criterions:
        already_get_value = False
        for s1 in set_1:
            if criterion.number == int(s1):
                value_1 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_1)
                value_2 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_2)
                already_get_value = True
        for s2 in set_2:
            if criterion.number == int(s2):
                value_1 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_1)
                value_2 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_2)
                already_get_value = True

        if already_get_value is False and larichev_question is True:
            try:
                value_1 = ValueOfPerfectAlternativePARK.objects.get(criteria=criterion,
                                                                    perfect_alternative=perfect_alternative)
                value_2 = value_1
                already_get_value = True
            except Exception as e:
                print(e)

        if already_get_value is True:
            if value_1.name != '':
                value_1 = f'{value_1.value} – ({value_1.name})'
            else:
                value_1 = value_1.value

            if value_2.name != '':
                value_2 = f'{value_2.value} – ({value_2.name})'
            else:
                value_2 = value_2.value

            new_alternative_1.append([f'K: {str(iter)}', value_1])
            new_alternative_2.append([f'K: {str(iter)}', value_2])
        iter += 1

    return new_alternative_1, new_alternative_2


def _update_quasi_order_pacom(option_id,  quasi_order_pacom):
    """Обновляем квазипорядок для опций равных или не сравнимых """

    pairs = PairsOfOptionsPARK.objects.filter(id_option_1=option_id, flag_winner_option=0) | \
           PairsOfOptionsPARK.objects.filter(id_option_1=option_id, flag_winner_option=3)

    for pair in pairs:
        Option.objects.filter(id=pair.id_option_2.id).update(quasi_order_pacom=quasi_order_pacom)

    pairs = PairsOfOptionsPARK.objects.filter(id_option_2=option_id, flag_winner_option=0) | \
           PairsOfOptionsPARK.objects.filter(id_option_2=option_id, flag_winner_option=3)

    for pair in pairs:
        Option.objects.filter(id=pair.id_option_1.id).update(quasi_order_pacom=quasi_order_pacom)


def _find_winner_in_pair(pair, result=None, is_not_comparable=False, option_2_is_empty=True, option_1_is_empty=True):
    if is_not_comparable:
        _update_pair_to_not_comparable(pair)

    if result is None:
        result = _is_comparable(pair, option_1_is_empty, option_2_is_empty)

    if pair.id_option_1.quasi_order_pacom == -1 and pair.id_option_2.quasi_order_pacom == -1:
        lose = 0
    elif pair.id_option_1.quasi_order_pacom > pair.id_option_2.quasi_order_pacom:
        lose = pair.id_option_1.quasi_order_pacom
    else:
        lose = pair.id_option_1.quasi_order_pacom

    if result == 1:
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_pacom=pair.quasi_level)
        option = Option.objects.get(id=pair.id_option_2.id)
        if option.quasi_order_pacom < lose:
            Option.objects.filter(id=pair.id_option_2.id).update(
                quasi_order_pacom=lose)

        PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                             flag_winner_option=1)
    elif result == 2:
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_pacom=pair.quasi_level)
        option = Option.objects.get(id=pair.id_option_1.id)
        if option.quasi_order_pacom < lose:
            Option.objects.filter(id=pair.id_option_1.id).update(
                quasi_order_pacom=lose)

        PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                             flag_winner_option=2)
    elif result == 0:
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_pacom=pair.quasi_level)
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_pacom=pair.quasi_level)

        PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                             flag_winner_option=0)
    else:
        _update_pair_to_not_comparable(pair)


def _checking_comparable(pair, set_1, set_2):
    pair = PairsOfOptionsPARK.objects.get(id=pair.id)
    compensable_option = pair.compensable_option

    if compensable_option == pair.id_option_1:
        if len(set_1) > 1:
            return False

    elif compensable_option == pair.id_option_2:
        if len(set_2) > 1:
            return False

    return True


def _fill_line_from_list(set: list) -> str:
    line = ''
    for s in set:
        if line == '':
            line = str(s)
        else:
            line = f'{line};{str(s)}'

    return line


def _update_pair_to_not_comparable(pair):
    # Делает пару не сравнимой
    Option.objects.filter(id=pair.id_option_1.id).update(
        quasi_order_pacom=pair.quasi_level)
    Option.objects.filter(id=pair.id_option_2.id).update(
        quasi_order_pacom=pair.quasi_level)

    PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=True,
                                                         flag_winner_option=3)


def _get_last_line(path):
    with open(path) as file:
        [last_line] = deque(file, maxlen=1) or ['']
    return last_line


def _is_comparable(pair, option_1_is_empty, option_2_is_empty):

    flag_1 = False
    flag_2 = False
    flag_0 = False
    flag_3 = False

    path = f'{MEDIA_ROOT}/files/models/{str(pair.id_model.id)}/pacom/PAIR{str(pair.id)}.txt'
    f = open(path)
    for line in f.readlines():
        temp_result = int(line.split('=')[1].split('\n')[0])
        set_1 = line.split('|')[0].split(';')
        set_2 = line.split('|')[1].split(';')

        if len(set_1) == 1 and len(set_2) == 1:
            if temp_result == 1:
                flag_1 = True
            elif temp_result == 2:
                flag_2 = True
            elif temp_result == 3:
               return 3
            else:
                flag_0 = True



    if flag_1 and flag_2:
        return 3
    elif flag_3:
        return 3
    elif flag_1 and not flag_2 and option_1_is_empty and not  option_2_is_empty:
        return 3
    elif flag_1 and not flag_2:
        return 1
    elif flag_2 and not flag_1 and  option_2_is_empty and not option_1_is_empty:
        return 3
    elif flag_2 and not flag_1:
        return 2
    elif flag_0 and option_1_is_empty and not  option_2_is_empty:
        return 2
    elif flag_0 and  option_2_is_empty and not option_1_is_empty:
        return 1
    elif not flag_1 and not flag_2 and not flag_0 and option_1_is_empty and not  option_2_is_empty:
        return 2
    elif not flag_1 and not flag_2 and not flag_0 and  option_2_is_empty and not option_1_is_empty:
        return 1
    else:
        return 0





def _write_history(pair, model, last_line, answer):
    if answer == 1:
        answer_to_history_model = 'Альтернатива №1 предпочтительнее'
    elif answer == 2:
        answer_to_history_model = 'Альтернатива №2 предпочтительнее'
    elif answer == 3:
        answer_to_history_model = 'Альтернативы не сравнимы'
    else:
        answer_to_history_model = 'Альтернатива одинаково предпочтительны'

    set_1 = last_line.split('|')[0].split(';')
    set_2 = last_line.split('|')[1].split('=')[0].split(';')

    left_list_of_values = ''
    right_list_of_values = ''

    for s in set_1:
        criterion = Criterion.objects.filter(number=int(s), id_model=model).first()
        value = Value.objects.filter(id_criterion=criterion, id_option=pair.id_option_1).first()
        if value.name != '':
            left_list_of_values += f' K:{criterion.name}: {value.value} – ({value.name})'
        else:
            left_list_of_values += f' K:{criterion.name}: {value.value}'

    for s in set_2:
        criterion = Criterion.objects.filter(number=int(s), id_model=model).first()
        value = Value.objects.filter(id_criterion=criterion, id_option=pair.id_option_2).first()
        if value.name != '':
            right_list_of_values += f' K:{criterion.name}: {value.value} – ({value.name})'
        else:
            right_list_of_values += f' K:{criterion.name}: {value.value}'

    question = f'{left_list_of_values} ? {right_list_of_values}'
    HistoryAnswerPACOM.objects.create(question=question, answer=answer_to_history_model, pair=pair, id_model=model)


def _add_1_to_number_of_question(model):
    Model.objects.filter(id=model.id).update(number_of_questions_pacom=model.number_of_questions_pacom + 1)


def get_winners_from_model(model):
    quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_pacom'))[
        'quasi_order_pacom__max']
    options_with_quasi_max_order = Option.objects.filter(quasi_order_pacom=quasi_max_order,
                                                         id_model=model)
    return {'flag_find_winner': True, 'winner_options': options_with_quasi_max_order}


def update_model_after_find_winner(model):
    time_end = datetime.datetime.now()
    try:
        time_begin = model.time_answer_pacom
        time_begin = datetime.datetime.strptime(time_begin, '%Y-%m-%d %H:%M:%S.%f')
        delta_time_many = time_end - time_begin
        delta_time_many = normalisation_time(delta_time_many)
    except:
        delta_time_many = 'Прошло 1 мин. 54 сек.'
    number_of_pairs = len(PairsOfOptionsPARK.objects.filter(id_model=model))
    number_of_incomparable = len(PairsOfOptionsPARK.objects.filter(id_model=model, flag_winner_option=3))

    Model.objects.filter(id=model.id).update(
        time_answer_pacom=delta_time_many,
        already_find_winner_PACOM=True,
        number_of_pairs=number_of_pairs,
        number_of_incomparable=number_of_incomparable
    )


# Возвращаем контекст истории ответов пользователей
def get_context_history_answer(model) -> list:

    pairs = PairsOfOptionsPARK.objects.filter(id_model=model)
    context = []

    for pair in pairs:

        item = {'pair': f'{pair.id_option_1.name} {pair.id_option_2.name}'}
        history_answers = HistoryAnswerPACOM.objects.filter(id_model=model, pair=pair)

        answers = []
        for answer_history in history_answers:
            answers.append({'question': answer_history.question, 'answer': answer_history.answer})
        item['body'] = answers

        if pair.flag_winner_option == 3:
            item['winner'] = 'Альтернативы не сравнимы'
        elif pair.flag_winner_option == 2:
            item['winner'] = f'Победитель: {pair.id_option_2.name}'
        if pair.flag_winner_option == 1:
            item['winner'] = f'Победитель: {pair.id_option_1.name}'
        if pair.flag_winner_option == 0:
            item['winner'] = 'Альтернативы одинаковы'
        context.append(item)

    return context


def auto_mode_range(input_data, request):
    try:
        context = {'range': True, 'compare': False}
        data = input_data['data']
        range_option_1 = 1
        range_option_2 = 1

        for d in data:
            if d['direction'] is True:
                if d['option_1'] < d['option_2']:
                    key = f'value_{str(d["criterion_id"])}_1'
                    context[key] = range_option_1
                    range_option_1 += 1
                elif d['option_1'] > d['option_2']:
                    key = f'value_{str(d["criterion_id"])}_2'
                    context[key] = range_option_2
                    range_option_2 += 1
            else:
                if d['option_1'] > d['option_2']:
                    key = f'value_{str(d["criterion_id"])}_1'
                    context[key] = range_option_1
                    range_option_1 += 1
                elif d['option_1'] < d['option_2']:
                    key = f'value_{str(d["criterion_id"])}_2'
                    context[key] = range_option_2
                    range_option_2 += 1
        context['pair'] = input_data['pair']
        return context

    except Exception as e:
        print(e)


def auto_mode_compare(input_data, auto_mode=False):
    import random
    post_context = {'pair': input_data['pair']}
    answer: int = random.randint(0, 3)
    post_context['answer'] = answer

    if auto_mode:
        return post_context
    else:
        request_obj(post_context)



def fix_quasi_order_pacom(model_id):
    """Правим квазипорядок после нахождения победителя"""
    n = Option.objects.filter(id_model=model_id).count()
    ni = 0
    model = Model.objects.filter(id=model_id).first()
    quasi_max_order_pacom = model.quasi_max_order_pacom

    real_quasi = 0
    for i in range(quasi_max_order_pacom+1):
        options = Option.objects.filter(id_model=model_id, quasi_order_pacom=i)
        if options:
            if real_quasi != i:
                for option in options:
                    o = Option.objects.get(id=option.id)
                    Option.objects.filter(id=o.id).update(quasi_order_pacom=real_quasi)
                    ni += 1
                    if ni == n:
                        Model.objects.filter(id=model_id).update(quasi_max_order_pacom=real_quasi)
                        options = Option.objects.filter(id_model=model_id)
                        for option in options:
                            print(f'{option.name} {str(option.quasi_order_pacom)}')
                        return
            real_quasi += 1
