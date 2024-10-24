translation = {
    ("*", "Current RES:"): "Выбранный RES:",
    ("Operator", "Select RES"): "Выбрать RES",
    ("*", "Select this res file"): "Выбрать этот RES файл",

    ("*", ('*.res file containing models, figures, animations, usually figures.res.\n'
           ' Click [...] then [ ✓ ] to select.')):
        ('*.res файл содержащий модели, фигуры, анимации, обычно figures.res.\n'
         ' Нажмите [...] , затем [ ✓ ] для выбора.'),

    ('*', 'If checked, packs model uvs/vcs more tightly, reducing mesh size by ~30%.'):
        "Если выбрано, упаковывает компоненты моделии более плотно, уменьшая размер файла на ~30%",

    ('*', 'ignore without morphs',):
        "игнорировать без морфов",
    ('*', 'If checked, skips export of meshes with some missing morphs',):
        "Если выбрано, пропускает экспорт мешей с неполными морф-коллекциями",

    ("*", 'Import %s meshes'): 'Импорт %s мешей',
    ("*", 'Import model/figure from selected RES into "base" collection.'):
        'Импорт модели/фигуры из выбранного RES в коллекцию "base"',
    ("*", 'Export %s meshes'): 'Экспорт %s мешей',
    ("*", ("Export models in base/morph collections into selected RES file.\n"
           "NOTE: Export needs all eight morph collections in the scene.\n"
           "NOTE: Morphing/shapekey (in original dragon/bat wings) animations run on top of base model\n")):
        'Экспортировать модели из коллекций "base"/морф в выбранный RES файл.\n'
        "N.B.: Требуются все восемь морф-коллекций в сцене.\n" \
        "N.B.: Морфанимации/шейпкей анимации (в оригинале крылья дракона, летучей мыши) работают относительно базовой модели.\n" \
        "Поэтому если морф компоненты от неё отличаются, анимации будут выглядеть неправильно",
    ("Operator", 'Clear scene'): 'Очистить сцену',
    ("Operator", "Optimize RES"): "Оптимизировать RES",
    ("*", "Recursively repack .res archive, reducing file size"): "Рекурсивно переупаковать RES, уменьшив размер файла",
    ("*", 'Model name to import/export, e.g. "unmodg".\n'
          'Leave empty and hit "import" to get list of importable models for current RES'):
        'Имя модели для импорта/экспорта, например "unmodg".\n'
        'Оставьте пустым и нажмите "импорт" для перечисления моделей, присутствующих в выбранном RES',
    ("*", 'Mesh mask'): 'Маска',
    ("*", "Comma-delimited mesh names for for partial import/export of a model.\n"
          "NOTE: RMB base collection objects to specifically import/export them"):
        "Список имен, разделенныхх запятой, для частичного импорта/экспорта модели. \n"
        "N.B.: ПКМ на объектах базовой коллекции позволяет экспортировать конкретно их",

    ("*", 'Create morphs for %s meshes'): 'Создать морфы для %s мешей',
    ("*", 'Generates morph components for existing "base" collection.\n' \
          'NOTE: applies R&S transforms to base collection ' \
          'which may break animation or model parent-child positioning'):
        'Создает морф-компоненты для коллекции "base"\n' \
        'N.B.: применяет трансформации вращения и масштаба к исходной коллекции, ' \
        'что может поломаать анимации или позиционирование чайлдов',

    ("Operator", "Drop .001 name part"): "Отбросить .001 в имени",
    ("*", 'Removes dot-numeric part from <*>.001 names to just <*>'):
        "Убирает .001-подобную часть из названий вида <*>.001 и т.д.",

    ("*", "as new collection"): "в новую коллекцию",
    ("*", 'Unchecked: import into base collection\n'
          'Checked: import into new copy of base collection named as animation'):
        ('Не выбрано: импорт в коллекцию "base"\n'
         'Выбрано: импорт в новую копию коллекции "base" с названием анимации'),
    ("*", "use mesh frame range"): "диапазон кадров из меша",
    ("*", ('For shapekey/export operations frame range (start, end)\n'
           'Checked: tries to calculate frame range from mesh animation\n'
           'Unchecked: uses scene frame range')):
        ('Диапазон кадров для шейпкеинга/экспорта анимации (начало, конец)\n'
         'Выбрано: пытается вычислить диапазон кадров из анимации меша\n'
         'Не выбрано: использует диапазон кадров сцены'),

    ("*", "Import animation into %s collection"): "Импортировать анимации в коллекцию %s",
    ("*", "Export animation from %s collection"): "Экспортировать анимации из коллекции %s",
    ("*", ('NOTE: Morphing/shapekey (in original dragon/bat wings) animations run on top of base model\n'
           'May want to keep their morphs identical to base')):
        ('N.B.: Морфанимации (в оригинале крылья дракона, летучей мыши) работают относительно базовой модели\n'
         'Вероятно, следует делать их морф-компоненты идентичными "base"'),

    ("*", "SRC: %s"): "ИСТОЧНИК: %s",
    ("*", "DEST: %s"): "ПРИЕМНИК: %s",
    ("Operator", "Animation to shapekeys"): "Анимация в шейпкеи",
    ("*", "Select SRC and DEST (the square-highlighted one)\n" \
          "Action will transfer SRC's vertex animation to DEST's shapekey animation"):
        "Выберите ИСТОЧНИК и ПРИЕМНИК (отмечен квадратом).\n" \
        "Анимеация ИСТОЧНИКА будет перенесена в шейпкеи ПРИЕМНИКА",

    ("Operator", "Bake transform"): "Запечь трансформации",
    ("*", 'For each object in selection, moves location / rotation / scale animation into shapekeys.\n' \
          'Ignores objects with shapekeys (morph animation)'):
        'Для каждого выбранного объекта, анимации перемещения / вращения / масштаба преобразуются в шейпкеи.\n' \
        'Объекты с шейпкеями игнорируются',

    ("Operator", "UE4 to shapekeys"): "UE4 в шейпкеи",
    ("*", 'Transform UE4 skeleton-animated model into shapekeyed mesh\n' \
          'Operates on root->armature->mesh structure, with root selected.'):
        'Преобразует UE4 скелетно-анимированную модель в шейпкееный меш.\n' \
        'Работает на структуре корень->арматура->меш, с выбранным корнем',

    ("*", "Model/Figure name is empty"): "Имя модели не задано",
    ("*", "RES file not found at: %s"): "RES файл не найден: %s",

}
locale = "ru_RU"
