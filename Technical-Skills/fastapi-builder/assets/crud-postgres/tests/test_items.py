def test_create_item(client):
    """Test creating an item"""
    response = client.post(
        "/items/",
        json={"name": "Test Item", "description": "A test item", "price": 19.99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 19.99
    assert "id" in data

def test_list_items(client):
    """Test listing items"""
    # Create a few items first
    client.post("/items/", json={"name": "Item 1", "price": 10.00})
    client.post("/items/", json={"name": "Item 2", "price": 20.00})

    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_get_item(client):
    """Test getting a specific item"""
    # Create item first
    create_response = client.post(
        "/items/",
        json={"name": "Get Test", "price": 15.00}
    )
    item_id = create_response.json()["id"]

    # Get the item
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test"

def test_get_nonexistent_item(client):
    """Test getting an item that doesn't exist"""
    response = client.get("/items/99999")
    assert response.status_code == 404

def test_update_item(client):
    """Test updating an item"""
    # Create item first
    create_response = client.post(
        "/items/",
        json={"name": "Original", "price": 10.00}
    )
    item_id = create_response.json()["id"]

    # Update the item
    response = client.put(
        f"/items/{item_id}",
        json={"name": "Updated", "price": 25.00}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["price"] == 25.00

def test_delete_item(client):
    """Test deleting an item"""
    # Create item first
    create_response = client.post(
        "/items/",
        json={"name": "To Delete", "price": 5.00}
    )
    item_id = create_response.json()["id"]

    # Delete the item
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 404

def test_pagination(client):
    """Test pagination"""
    # Create multiple items
    for i in range(15):
        client.post("/items/", json={"name": f"Item {i}", "price": float(i)})

    # Test default pagination
    response = client.get("/items/")
    assert response.status_code == 200
    assert len(response.json()) == 10  # Default limit

    # Test custom pagination
    response = client.get("/items/?skip=5&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
