# Touch Service Config Guide

Use this guide to convert `docs/CLIENT_INTAKE_FORM.md` answers into Touch
service and package configuration.

## Service Fields

Each bookable service needs these fields:

- `id`: stable technical key used by backend/frontend. Use lowercase ASCII,
  snake_case, no spaces. Example: `classic_back`.
- `title`: client-facing service title. Keep RU and UK variants where the app
  supports both languages.
- `duration`: service duration in minutes for one session.
- `price`: one-session price in EUR.
- `description`: short client-facing Mini App description. Keep RU and UK
  variants. Do not put text from images here.
- `category`: optional grouping label for future filtering/reporting. Example:
  `massage`, `wellness`, `child`, `package`.

Recommended source mapping:

| Intake field | Service config field |
| --- | --- |
| Service name in Russian/Ukrainian | `title` |
| Duration in minutes | `duration` |
| Price in EUR | `price` |
| Short Mini App description | `description` |
| Special notes/age limits | `description` or safety note |
| Online booking availability | include/exclude from client list |

## Package Fields

Each package/course should be tied to a base service and include:

- `sessions_total`: total number of sessions in the package.
- `old_price`: regular total price without discount.
- `package_price`: discounted package price in EUR.
- `discount_percent`: discount shown to the client.

Recommended calculation:

```text
old_price = one_session_price * sessions_total
discount_percent = ((old_price - package_price) / old_price) * 100
```

Round `discount_percent` to one decimal only when needed. Use whole numbers
when the result is clean.

## Booking Format Rules

The Mini App should present booking format options after the client opens a
service detail screen:

- `1 session`: use the base service `id`, base duration, and one-session price.
- `5 sessions`: use a package variant with `sessions_total = 5`.
- `10 sessions`: use a package variant with `sessions_total = 10`.

Rules:

- Keep package IDs stable and derived from the base service ID.
- Suggested pattern: `{service_id}_package_5` and `{service_id}_package_10`.
- Packages should not receive first-visit bonus unless explicitly approved.
- Package purchase can create package balance, but booking still needs a real
  date/time slot.
- Completed package visits may deduct from package balance.
- No-show and cancellation deductions must follow the client's package policy.

## Wellness-Only Wording Rules

Use wellness wording when the service is not medical or therapeutic.

Use:

- Relaxation
- Comfort
- Lightness
- General wellbeing
- Muscle tension relief in a non-medical sense
- Self-care
- Recovery of ease after everyday activity

Avoid:

- Treatment
- Cure
- Diagnosis
- Medical result promises
- Pain cure claims
- Rehabilitation claims unless the provider is licensed and the client approves
  exact wording

Preferred disclaimer:

```text
This massage is not a medical or therapeutic procedure.
```

For RU/UK client text, keep the same meaning:

- RU: `Массаж не является медицинской или лечебной процедурой.`
- UK: `Масаж не є медичною або лікувальною процедурою.`

## Child Massage Safety Wording Rules

For child massage services, always collect and show age/safety constraints.

Required ideas:

- Age range, for example `7-13`.
- Gentle wellness massage wording.
- Child comfort and consent.
- Parent/guardian presence.
- Not medical or therapeutic.

Recommended UK short text:

```text
М'який велнес-масаж для дітей 7-13 років для розслаблення, комфорту та
відчуття легкості. Проводиться делікатно, тільки за згодою і в присутності
батьків. Не є медичною або лікувальною процедурою.
```

Recommended RU short text:

```text
Мягкий велнес-массаж для детей 7-13 лет для расслабления, комфорта и ощущения
легкости. Проводится деликатно, только с согласия и в присутствии родителей. Не
является медицинской или лечебной процедурой.
```

Do not make child massage sound like a medical service unless the client has a
clear legal basis and explicitly approves the wording.

## Language And i18n Requirements

- Client Mini App UI supports `ru` and `uk`.
- Use frontend language code `uk`, not `ua`.
- Backend may accept `uk` or `ua`.
- Select Ukrainian only when `Telegram.WebApp.initDataUnsafe.user.language_code`
  starts with `uk`; otherwise default to Russian.
- Service titles and descriptions must have RU and UK versions.
- Admin bot text must stay Russian.
- Google Calendar titles/descriptions must stay Russian.
- Internal technical keys must not be localized.
- Do not use localized client service titles for admin summaries if a stable
  admin/RU title is required.

## Current Service Examples

### Classic Back Massage

```text
id: classic_back
category: massage
RU title: Классический массаж спины
UK title: Класичний масаж спини
duration: 45
price: 20
```

Packages:

```text
classic_back_package_5:
  sessions_total: 5
  old_price: 100
  package_price: 90
  discount_percent: 10

classic_back_package_10:
  sessions_total: 10
  old_price: 200
  package_price: 175
  discount_percent: 12.5
```

### Relax Massage

```text
id: relax
category: massage
RU title: Релакс-массаж
UK title: Релакс-масаж
duration: 45
price: 20
```

Packages:

```text
relax_package_5: 5 sessions, 90 EUR instead of 100 EUR, 10%
relax_package_10: 10 sessions, 175 EUR instead of 200 EUR, 12.5%
```

### Anti-Cellulite Massage

```text
id: anti_cellulite
category: massage
RU title: Антицеллюлитный массаж
UK title: Антицелюлітний масаж
duration: 45
price: 30
```

Packages:

```text
anti_cellulite_package_5: 5 sessions, 135 EUR instead of 150 EUR, 10%
anti_cellulite_package_10: 10 sessions, 260 EUR instead of 300 EUR, 13.3%
```

### Sport Massage

```text
id: sport
category: massage
RU title: Спортивный массаж
UK title: Спортивний масаж
duration: 45
price: 30
```

Packages:

```text
sport_package_5: 5 sessions, 135 EUR instead of 150 EUR, 10%
sport_package_10: 10 sessions, 260 EUR instead of 300 EUR, 13.3%
```

### General Massage

```text
id: general
category: massage
RU title: Общий массаж
UK title: Загальний масаж
duration: 90
price: 70
```

Current package examples:

```text
general_package_5: 5 sessions, 180 EUR instead of 200 EUR, 10%
general_package_10: 10 sessions, 350 EUR instead of 400 EUR, 12.5%
```

Before launch, verify whether package prices should follow the current base
price of 70 EUR or a custom client-approved package table.

### Child Wellness Massage

```text
id: child_wellness
category: child
RU title: Детский велнес-массаж
UK title: Дитячий велнес-масаж
duration: 30
price: 15
age: 7-13
```

Packages:

```text
child_wellness_package_5: 5 sessions, 60 EUR instead of 75 EUR, 20%
child_wellness_package_10: 10 sessions, 130 EUR instead of 150 EUR, 13.3%
```

Safety wording must mention parent/guardian presence and that the service is
not medical or therapeutic.

## Validation Checklist Before Launch

- Every service has a stable ASCII `id`.
- Every package ID is derived from its base service ID.
- RU and UK titles exist for every client-facing service.
- RU and UK descriptions exist for every client-facing service.
- Durations are in minutes and match booking slot rules.
- Prices are in EUR and match the client-approved price table.
- Package `old_price` equals one-session price times `sessions_total`, unless
  the client explicitly approved a different old price.
- `discount_percent` is mathematically correct and displayed consistently.
- Packages exist only for services where the client approved packages.
- Child services include age, consent, parent/guardian presence, and wellness
  disclaimer.
- Wellness services avoid medical treatment claims.
- Admin and Google Calendar text remains Russian.
- Technical status values and service IDs are not localized.
- Services hidden from online booking are not shown in the Mini App client list.
- Test one regular service booking.
- Test one 5-session package booking.
- Test one 10-session package booking.
- Test service display in RU Telegram language.
- Test service display in UK Telegram language.
