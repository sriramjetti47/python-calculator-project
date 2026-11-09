import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Python Calculator" in response.data or b"Calculator" in response.data


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3", 5),
        ("10 - 4", 6),
        ("6 * 7", 42),
        ("20 / 5", 4),
        ("(2 + 3) * 4", 20),
        ("-5 + 2", -3),
        ("2 ** 3", 8),
    ],
)
def test_valid_calculations(client, expression, expected):
    response = client.post("/calculate", json={"expression": expression})
    assert response.status_code == 200
    assert response.get_json()["result"] == expected


def test_division_by_zero_returns_bad_request(client):
    response = client.post("/calculate", json={"expression": "5 / 0"})
    assert response.status_code == 400
    assert "error" in response.get_json()


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo unsafe')",
        "open('/etc/passwd').read()",
        "2 + unknown",
        "",
        "1" * 101,
    ],
)
def test_invalid_expressions_are_rejected(client, expression):
    response = client.post("/calculate", json={"expression": expression})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_missing_expression_is_rejected(client):
    response = client.post("/calculate", json={})
    assert response.status_code == 400
