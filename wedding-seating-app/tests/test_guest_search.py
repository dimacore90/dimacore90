from app.google_sheets import find_guest, normalize_name, sort_guests
from app.models import Guest


def test_normalize_name_ignores_case_and_extra_spaces():
    assert normalize_name("  АнНА   ИвАнОвА  ") == "анна иванова"


def test_find_guest_matches_name_without_case_or_double_spaces():
    guests = [
        Guest(first_name="Анна", last_name="Иванова", table_number=1),
        Guest(first_name="Иван", last_name="Петров", table_number=2),
    ]

    guest = find_guest("  анна", "ИВАНОВА  ", guests)

    assert guest is not None
    assert guest.table_number == 1


def test_find_guest_returns_none_for_unknown_guest():
    guests = [Guest(first_name="Анна", last_name="Иванова", table_number=1)]

    assert find_guest("Мария", "Смирнова", guests) is None


def test_sort_guests_orders_by_last_name_then_first_name():
    guests = [
        Guest(first_name="Иван", last_name="Петров", table_number=2),
        Guest(first_name="Анна", last_name="Иванова", table_number=1),
        Guest(first_name="Борис", last_name="Иванов", table_number=3),
    ]

    sorted_names = [(guest.last_name, guest.first_name) for guest in sort_guests(guests)]

    assert sorted_names == [
        ("Иванов", "Борис"),
        ("Иванова", "Анна"),
        ("Петров", "Иван"),
    ]
