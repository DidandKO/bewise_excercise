from tempfile import NamedTemporaryFile
import shutil
import csv
import pymorphy2 as morph


temp_file = NamedTemporaryFile(mode='w', delete=False, newline="")
FILE_NAME = 'test_data - test_data.csv'
NEW_FILE = 'td.csv'
INTENTS = {
    'greeting': {'здравств': None, 'добр': ['ден', 'дня', 'вечер']},
    'manager_name_present': [['меня', 'зовут'], ['мое', 'имя']],
    'company_name': ['компания', 'фирма'],
    'parting': {'до': ['свидания', 'связи', 'завтра'], 'всего': ['хорошего', 'доброго'],
                'хорошего': ['дня', 'вечера']}
}


def _format_line_to_lower(text):
    format_text = text.lower()
    return format_text


def check_greeting(line):
    new_line = _format_line_to_lower(line).split()
    for greet in INTENTS['greeting']:
        for word in new_line:
            if greet in word:
                if INTENTS['greeting'][greet]:
                    for sub_greet in INTENTS['greeting'][greet]:
                        for word in new_line:
                            if sub_greet in word:
                                return True
                else:
                    return True
    return False


def check_manager_name_present(line):
    words = _format_line_to_lower(line).split()
    for word in words:
        for cases in INTENTS['manager_name_present']:
            for case in cases:
                if case in word:
                    return True
    return False


def get_manager_name(line):
    tresh = 0.6
    words = _format_line_to_lower(line).split()
    for name in words:
        name = morph.MorphAnalyzer().parse(name)
        if 'Name' in name[0].tag and name[0].score >= tresh:
            return name[0].normal_form


def get_company_name(line):
    result = []
    words = _format_line_to_lower(line).split()
    for word_index, word in enumerate(words):
        if word in INTENTS['company_name']:
            i = 1
            company_name = morph.MorphAnalyzer().parse(words[word_index + i])
            while 'NOUN' in company_name[0].tag or 'ADJF' in company_name[0].tag:
                result.append(words[word_index + i])
                i += 1
                company_name = morph.MorphAnalyzer().parse(words[word_index + i])
    return ' '.join(result)


def check_parting(line):
    new_line = _format_line_to_lower(line).split()
    for parting in INTENTS['parting']:
        for word in new_line:
            if parting in word:
                if INTENTS['parting'][parting]:
                    for sub_greet in INTENTS['parting'][parting]:
                        for word in new_line:
                            if sub_greet in word:
                                return True
                else:
                    return True
    return False


def main():
    with open(FILE_NAME, 'r', encoding='utf8') as csv_file, temp_file:
        reader = csv.reader(csv_file)
        headers = next(reader)
        headers.append('insights')
        writer = csv.DictWriter(temp_file, fieldnames=headers)
        headers_row = {'dlg_id': 'dlg_id', 'line_n': 'line_n', 'role': 'role',
                                   'text': 'text', 'insights': 'insights'}
        writer.writerow(headers_row)
        dlg_data = {}

        for dlg_id, line_n, speaker, fraze in reader:
            updated_row = {'dlg_id': dlg_id, 'line_n': line_n, 'role': speaker,
                           'text': fraze, 'insights': []}
            if speaker == 'manager':
                stored_line = any([check_greeting(fraze), check_manager_name_present(fraze), check_parting(fraze),
                                   get_company_name(fraze)])
                if stored_line:
                    print(f'{speaker}: {fraze}')
                    dlg_data[f'{dlg_id}:{line_n}'] = {}
                else:
                    updated_row['insights'].append('')
                if check_greeting(fraze):
                    print(f'Приветствия: {check_greeting(fraze)}, диалог {dlg_id}, строка {line_n}')
                    dlg_data[f'{dlg_id}:{line_n}']['greeting'] = check_greeting(fraze)
                    updated_row['insights'].append(f'greeting:{check_greeting(fraze)}')
                if check_manager_name_present(fraze):
                    print(f'Диалог {dlg_id}, строка {line_n}, менеджер представился?: {check_manager_name_present(fraze)}')
                    dlg_data[f'{dlg_id}:{line_n}']['name_present'] = check_manager_name_present(fraze)
                    updated_row['insights'].append(f'manager_name_present:{check_manager_name_present(fraze)}')
                if check_manager_name_present(fraze):
                    print(f'Имя менеджера: {get_manager_name(fraze)}, диалог {dlg_id}, строка {line_n}')
                    dlg_data[f'{dlg_id}:{line_n}']['manager_name'] = get_manager_name(fraze)
                    updated_row['insights'].append(f'manager_name:{get_manager_name(fraze)}')
                if get_company_name(fraze):
                    print(f'Название компании: {get_company_name(fraze)}, диалог {dlg_id}, строка {line_n}')
                    dlg_data[f'{dlg_id}:{line_n}']['company_name'] = get_company_name(fraze)
                    updated_row['insights'].append(f'company_name:{get_company_name(fraze)}')
                if check_parting(fraze):
                    print(f'Прощания: {check_parting(fraze)}, диалог {dlg_id}, строка {line_n}')
                    dlg_data[f'{dlg_id}:{line_n}']['parting'] = check_parting(fraze)
                    updated_row['insights'].append(f'parting:{check_parting(fraze)}')
                print()
            else:
                updated_row['insights'].append('')
            writer.writerow(updated_row)

    with open(NEW_FILE, mode='w', encoding='utf8', newline=""):
        shutil.move(temp_file.name, NEW_FILE)

    print(dlg_data)
    return dlg_data


if __name__ == '__main__':
    main()
