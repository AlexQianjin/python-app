from app.main import app


def test_product_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/products" in paths
    assert "/api/products/summary" in paths
    assert "/api/products/{product_id}" in paths


def test_cart_and_order_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/cart" in paths
    assert "/api/cart/items" in paths
    assert "/api/cart/items/{item_id}" in paths
    assert "/api/orders" in paths
    assert "/api/orders/{order_id}" in paths
