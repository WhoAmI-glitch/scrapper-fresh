# Дизайн-система LeadFlow

Профессиональная B2B SaaS платформа для сбора и обогащения данных строительных компаний.

---

## 📐 Архитектура интерфейса

### Структура макета

```
┌─────────────────────────────────────────────────────┐
│  Top Bar (Логотип | Название | Поиск | Профиль)    │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ Sidebar  │  Main Content Area                       │
│          │  ┌────────────────────────────────────┐  │
│ - Главная│  │ Dashboard Cards (Метрики)          │  │
│ - Лиды   │  └────────────────────────────────────┘  │
│ - Очередь│  ┌────────────────────────────────────┐  │
│ - Экспорт│  │ Progress Bar + Actions             │  │
│ - Помощь │  └────────────────────────────────────┘  │
│          │  ┌────────────────────────────────────┐  │
│          │  │ Data Table (Лиды)                  │  │
│          │  └────────────────────────────────────┘  │
└──────────┴──────────────────────────────────────────┘
```

### Компоненты

- **Sidebar** (260px): Навигация, логотип, футер
- **Top Bar** (64px): Заголовок страницы, профиль пользователя
- **Content Area**: Основной контент с карточками, таблицами, кнопками

---

## 🎨 Цветовая система

### Основная палитра

```css
/* Основные цвета */
--color-primary: #1B3A57;         /* Тёмно-синий (основной) */
--color-primary-dark: #14293F;    /* Тёмно-синий (hover) */
--color-primary-light: #2D5F7F;   /* Средний синий */

/* Акценты */
--color-accent: #10B981;          /* Изумрудный (успех) */
--color-accent-dark: #059669;     /* Изумрудный (hover) */
--color-warning: #F59E0B;         /* Янтарный */
--color-error: #EF4444;           /* Красный */
--color-info: #3B82F6;            /* Голубой */
```

### Нейтральные цвета

```css
/* Фоны */
--color-bg-primary: #F7F9FC;      /* Светлый фон */
--color-bg-surface: #FFFFFF;      /* Белый (карточки) */
--color-bg-sidebar: #1F2937;      /* Тёмно-серый (sidebar) */

/* Текст */
--color-text-primary: #1F2937;    /* Основной текст */
--color-text-secondary: #6B7280;  /* Вторичный текст */
--color-text-muted: #9CA3AF;      /* Приглушённый текст */
--color-text-inverse: #FFFFFF;    /* Белый текст */

/* Границы */
--color-border: #E5E7EB;          /* Основные границы */
--color-border-light: #F3F4F6;    /* Светлые границы */
```

### Тени

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
```

### Применение цветов

| Элемент                | Цвет                     | Использование                |
|------------------------|--------------------------|------------------------------|
| Основные кнопки        | `color-primary`          | CTA, основные действия       |
| Успешные действия      | `color-accent`           | Подтверждения, завершённые   |
| Предупреждения         | `color-warning`          | В процессе, ожидание         |
| Ошибки                 | `color-error`            | Неудачи, критичные события   |
| Информация             | `color-info`             | Новые элементы, нейтральные  |
| Фон страницы           | `color-bg-primary`       | Основной фон приложения      |
| Карточки               | `color-bg-surface`       | Белый фон для карточек       |
| Боковая панель         | `color-bg-sidebar`       | Тёмная навигация             |

---

## 📝 Типографика

### Шрифт

```css
--font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

**Рекомендация**: Использовать [Inter](https://fonts.google.com/specimen/Inter) через Google Fonts для профессионального вида.

### Размеры

```css
--text-xs: 12px;      /* Метки, timestamps, вспомогательный текст */
--text-sm: 14px;      /* Основной текст, описания */
--text-base: 16px;    /* Body, параграфы */
--text-lg: 18px;      /* H3, подзаголовки */
--text-xl: 20px;      /* H2, заголовки секций */
--text-2xl: 24px;     /* H1, главные заголовки */
--text-3xl: 28px;     /* Hero, крупные заголовки */
```

### Иерархия

```css
/* H1 - Главные заголовки страниц */
h1 {
    font-size: var(--text-2xl);
    font-weight: 600;
    line-height: 1.2;
}

/* H2 - Заголовки секций */
h2 {
    font-size: var(--text-xl);
    font-weight: 600;
    line-height: 1.3;
}

/* H3 - Заголовки карточек */
h3 {
    font-size: var(--text-lg);
    font-weight: 600;
    line-height: 1.4;
}

/* Body - Основной текст */
body {
    font-size: var(--text-base);
    line-height: 1.5;
}
```

---

## 🧩 Компоненты

### 1. Карточки метрик

**Назначение**: Отображение ключевых показателей (KPI).

**Структура**:
- Иконка (40x40px, цветной фон)
- Метка (uppercase, 14px, серый)
- Значение (24px, жирный, чёрный)
- Описание (14px, приглушённый)

**CSS**:
```css
.metric-card {
    background: var(--color-bg-surface);
    border-radius: var(--border-radius-lg);
    padding: var(--space-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--color-border-light);
}

.metric-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}
```

**Пример**:
```html
<div class="metric-card">
    <div class="metric-header">
        <div class="metric-label">Всего лидов</div>
        <div class="metric-icon primary">📊</div>
    </div>
    <div class="metric-value">1,247</div>
    <div class="metric-description">Обогащённых компаний</div>
</div>
```

---

### 2. Кнопки

**Типы кнопок**:

| Тип         | Класс           | Цвет              | Использование                     |
|-------------|-----------------|-------------------|-----------------------------------|
| Primary     | `.btn-primary`  | `color-primary`   | Основные действия (Запустить)    |
| Success     | `.btn-success`  | `color-accent`    | Положительные действия (Готово)  |
| Export      | `.btn-export`   | Градиент фиолетовый | Экспорт данных                  |

**CSS**:
```css
.btn {
    padding: 14px 24px;
    border: none;
    border-radius: var(--border-radius-md);
    font-size: var(--text-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: var(--shadow-sm);
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}
```

**Пример**:
```html
<button class="btn btn-primary">
    <span class="btn-icon">▶️</span>
    <span>Запустить сбор</span>
</button>
```

---

### 3. Статусные бейджи

**Назначение**: Отображение состояния задач/лидов.

**Статусы**:

| Статус    | Класс             | Цвет           | Текст        |
|-----------|-------------------|----------------|--------------|
| Новый     | `.status-badge.new` | `color-info`   | Новый        |
| Загрузка  | `.status-badge.fetching` | `color-warning` | Загрузка |
| Парсинг   | `.status-badge.parsed` | `#8B5CF6` (фиолетовый) | Парсинг |
| Готово    | `.status-badge.done` | `color-accent` | Готово      |
| Ошибка    | `.status-badge.failed` | `color-error`  | Ошибка      |

**CSS**:
```css
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    padding: 4px 12px;
    border-radius: 100px;
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
}

.status-badge.done {
    background: rgba(16, 185, 129, 0.1);
    color: var(--color-accent);
}
```

**Пример**:
```html
<span class="status-badge done">
    <span class="status-dot"></span>
    Готово
</span>
```

---

### 4. Таблицы

**Назначение**: Отображение списков лидов.

**Особенности**:
- Фиксированный заголовок (sticky header)
- Чередующийся фон строк
- Hover-эффект на строках
- Цветные статусы

**CSS**:
```css
table {
    width: 100%;
    border-collapse: collapse;
}

thead {
    background: var(--color-bg-primary);
    position: sticky;
    top: var(--topbar-height);
    z-index: 10;
}

th {
    padding: 12px var(--space-md);
    text-align: left;
    font-size: var(--text-xs);
    font-weight: 700;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

tbody tr:hover {
    background: var(--color-bg-primary);
}

tbody tr:nth-child(even) {
    background: rgba(247, 249, 252, 0.5);
}
```

---

### 5. Уведомления (Alerts)

**Типы**:

| Тип       | Класс          | Фон         | Граница        | Использование             |
|-----------|----------------|-------------|----------------|---------------------------|
| Success   | `.alert.success` | `#D1FAE5`   | `color-accent` | Успешное завершение       |
| Error     | `.alert.error`   | `#FEE2E2`   | `color-error`  | Ошибки                    |
| Info      | `.alert.info`    | `#DBEAFE`   | `color-info`   | Информационные сообщения  |

**CSS**:
```css
.alert {
    padding: var(--space-md) var(--space-lg);
    border-radius: var(--border-radius-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);
    border-left: 4px solid;
    box-shadow: var(--shadow-sm);
}

.alert.success {
    background: #D1FAE5;
    color: #065F46;
    border-left-color: var(--color-accent);
}
```

**Пример**:
```html
<div class="alert success">
    <span class="alert-icon">✓</span>
    <span>Сбор завершён успешно: 8 кандидатов найдено</span>
</div>
```

---

### 6. Прогресс-бар

**Назначение**: Отображение прогресса обработки задач.

**Структура**:
- Заголовок + процент
- Полоса прогресса (8px высота, скруглённая)
- Описание (выполнено / всего)

**CSS**:
```css
.progress-bar-container {
    width: 100%;
    height: 8px;
    background: var(--color-bg-primary);
    border-radius: 100px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--color-accent) 0%, var(--color-accent-dark) 100%);
    border-radius: 100px;
    transition: width 0.3s ease;
}
```

**Пример**:
```html
<div class="progress-section">
    <div class="progress-header">
        <div class="progress-title">Прогресс обработки</div>
        <div class="progress-percentage">75%</div>
    </div>
    <div class="progress-bar-container">
        <div class="progress-bar" style="width: 75%"></div>
    </div>
    <div class="progress-details">
        150 из 200 задач выполнено
    </div>
</div>
```

---

## 📏 Spacing System

```css
--space-xs: 4px;    /* Минимальные отступы */
--space-sm: 8px;    /* Малые отступы */
--space-md: 16px;   /* Средние отступы */
--space-lg: 24px;   /* Большие отступы */
--space-xl: 32px;   /* Очень большие отступы */
```

**Применение**:
- `xs`: Gap между иконкой и текстом в бейдже
- `sm`: Padding внутри малых элементов
- `md`: Стандартный padding карточек
- `lg`: Padding больших секций
- `xl`: Margin между секциями

---

## 🎭 Микро-взаимодействия

### Hover-эффекты

```css
/* Карточки */
.metric-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    transition: all 0.3s;
}

/* Кнопки */
.btn:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

/* Строки таблицы */
tbody tr:hover {
    background: var(--color-bg-primary);
}
```

### Анимации

```css
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn 0.3s ease;
}
```

---

## 📱 Адаптивность

### Breakpoints

```css
/* Desktop: >= 1024px (по умолчанию) */
/* Tablet: 768px - 1023px */
/* Mobile: < 768px */

@media (max-width: 768px) {
    .sidebar {
        width: 70px; /* Компактная боковая панель */
    }

    .metrics-grid {
        grid-template-columns: 1fr; /* Одна колонка */
    }

    .nav-item span {
        display: none; /* Скрываем текст в навигации */
    }
}
```

---

## ✅ Чеклист внедрения

### Обязательные требования

- [ ] Все тексты на русском языке
- [ ] Использование CSS-переменных из дизайн-системы
- [ ] Адаптивность для мобильных устройств
- [ ] Hover-эффекты на интерактивных элементах
- [ ] Корректная цветовая схема (не generic blue)
- [ ] Профессиональная типографика (Inter или система)
- [ ] Статусные бейджи с правильными цветами
- [ ] Тени для глубины (shadow-sm, shadow-md)
- [ ] Скруглённые углы (8-12px)
- [ ] Консистентные отступы (spacing system)

### Рекомендуемые улучшения

- [ ] Подключение шрифта Inter через Google Fonts
- [ ] Анимации появления элементов (fade-in)
- [ ] Loading-индикаторы для долгих операций
- [ ] Toast-уведомления вместо alert
- [ ] Фильтры и поиск в таблице
- [ ] Пагинация для больших списков
- [ ] Экспорт с выбором полей
- [ ] Dark mode (опционально)

---

## 🎨 Цветовые комбинации

### Основные сценарии

**Успешное действие**:
- Фон: `#D1FAE5` (светло-зелёный)
- Текст: `#065F46` (тёмно-зелёный)
- Граница: `#10B981` (изумрудный)

**Предупреждение**:
- Фон: `#FEF3C7` (светло-жёлтый)
- Текст: `#92400E` (коричневый)
- Граница: `#F59E0B` (янтарный)

**Ошибка**:
- Фон: `#FEE2E2` (светло-красный)
- Текст: `#991B1B` (тёмно-красный)
- Граница: `#EF4444` (красный)

**Информация**:
- Фон: `#DBEAFE` (светло-голубой)
- Текст: `#1E40AF` (тёмно-синий)
- Граница: `#3B82F6` (голубой)

---

## 🚀 Быстрый старт

### 1. Подключить шаблон

```python
# src/scrapper/web/app.py
return templates.TemplateResponse(
    "dashboard_v2.html",  # Новый шаблон
    {
        "request": request,
        "stats": stats,
        "message": message,
        "message_type": message_type,
    },
)
```

### 2. Перезапустить Docker

```bash
docker compose up -d --build
```

### 3. Открыть в браузере

```
https://localhost/ui/
```

---

## 📚 Ресурсы

- **Шрифт**: [Inter на Google Fonts](https://fonts.google.com/specimen/Inter)
- **Иконки**: Можно использовать emoji или [Heroicons](https://heroicons.com/)
- **Цвета**: Палитра основана на [Tailwind CSS](https://tailwindcss.com/docs/customizing-colors)
- **Компоненты**: Вдохновлены [Stripe Dashboard](https://dashboard.stripe.com/) и [Notion](https://www.notion.so/)

---

## 🎯 Принципы дизайна

1. **Чистота**: Минимум визуального шума, максимум информации
2. **Иерархия**: Ясная структура контента (заголовки → метрики → таблицы)
3. **Консистентность**: Единый стиль во всех компонентах
4. **Профессионализм**: Сдержанная палитра, без ярких градиентов
5. **Функциональность**: Каждый элемент имеет чёткую цель

---

**Дизайн-система LeadFlow** — это основа для создания профессионального, масштабируемого и удобного интерфейса российской B2B SaaS платформы.
