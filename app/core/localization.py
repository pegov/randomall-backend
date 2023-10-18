from app.config import LANGUAGE

if LANGUAGE == "RU":
    t = {
        "SERVER_ERROR": "Серверная ошибка",
        "head": {
            "labels": {
                "title": "Название",
                "description": "Описание",
                "access": "Доступ",
                "tags": "Тэги",
                "category": "Категория",
                "subcategories": "Подкатегории",
            },
            "errors": {
                "title_blank": "Не может быть пустым",
                "title_too_long": "Не больше 256 символов",
                "description_blank": "Не может быть пустым",
                "description_too_long": "Не больше 1000 символов",
                "access_error": "Неверное значение доступа",
                "tags_blank": "Введите тэги",
                "tags_too_many": "Слишком много тэгов",
                "tags_error": "Ошибка в тэгах",
                "category_blank": "Выберите категорию",
                "category_error": "Неверная категория",
                "subcategories_too_many": "Слишком много подкатегорий",
            },
        },
        "format": {
            "labels": {
                "align": "Выравнивание",
                "errors": {
                    "align_error": "Неверное значение выравнивания",
                },
            }
        },
        "body": {
            "blocks": {
                "labels": {
                    "sequences": "Последовательности",
                    "exceptions": "Исключения",
                    "content": "Контент",
                    "before": "Текст до",
                    "after": "Текст после",
                    "block": "Блок",
                    "end": "Конец блока",
                },
                "errors": {
                    "before_after_too_long": "Не больше 1000 символов",
                    "slicer_error": "Неверный разделитель",
                    "content_blank": "Не может быть пустым",
                    "content_too_long": "Слишком много символов (не больше 100000).",
                    "end_error": "Неверный конец блока",
                    "align_error": "Неверное значение",
                    "mods_fix_blocks": "Что-то не так...",
                    "mods_error_1": "Ошибка в последовательности # {i}",
                    "mods_error_2": "Ошибка в последовательности # {i}, кол-во блоков: {blocks_count}, неверный номер блока: {n}",
                },
            }
        },
    }
else:
    t = {
        "SERVER_ERROR": "Server error",
        "head": {
            "labels": {
                "title": "Title",
                "description": "Description",
                "access": "Access",
                "tags": "Tags",
                "category": "Category",
                "subcategories": "Subcategories",
            },
            "errors": {
                "title_blank": "Can't be blank",
                "title_too_long": "No more than 256 symbols",
                "description_blank": "Can't be blank",
                "description_too_long": "No more than 1000 symbols",
                "access_error": "Wrong value",
                "tags_blank": "Enter tags",
                "tags_too_many": "Too many tags",
                "tags_error": "Error in tags",
                "category_blank": "Choose category",
                "category_error": "Wrong category",
                "subcategories_too_many": "Too many subcategories",
            },
        },
        "format": {
            "labels": {
                "align": "Align",
                "errors": {
                    "align_error": "Wrong align value",
                },
            }
        },
        "body": {
            "blocks": {
                "labels": {
                    "sequences": "Sequences",
                    "exceptions": "Exceptions",
                    "content": "Content",
                    "before": "Before",
                    "after": "After",
                    "block": "Block",
                    "end": "End",
                },
                "errors": {
                    "before_after_too_long": "No more than 1000 symbols",
                    "slicer_error": "Wrong slicer",
                    "content_blank": "Can't be blank",
                    "content_too_long": "Too many symbols",
                    "end_error": "Wrong block end",
                    "align_error": "Wrong value",
                    "mods_fix_blocks": "Something went wrong...",
                    "mods_error_1": "Error in # {i}",
                    "mods_error_2": "Error in # {i}, blocks count: {blocks_count}, error in block: {n}",
                },
            }
        },
    }
