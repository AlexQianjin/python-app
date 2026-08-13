from app.main import app


def test_product_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/products" in paths
    assert "/api/products/summary" in paths
    assert "/api/products/{product_id}" in paths
