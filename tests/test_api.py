def test_create_user(api):
    response = api.post("/users", data={"name": "Asha"})
    assert response.status == 201
    body = response.json()
    assert body["name"] == "Asha"
    assert body["balance"] == 0

def test_deposit_increases_balance(api):
    # 1. Create a user and remember their id
    user = api.post("/users", data={"name": "Ravi"}).json()
    user_id = user["user_id"]
    # 2. Deposit 100 into that user's account
    response = api.post(f"/users/{user_id}/transactions",
                        data={"type": "DEPOSIT", "amount": 100})
    assert response.status == 201
    # 3. Check the balance went up
    balance = api.get(f"/users/{user_id}").json()["balance"]
    assert balance == 100

def test_withdraw_more_than_balance_negative(api):
   # 1. Create a user and remember their id
    user = api.post("/users", data={"name": "Apoorva"}).json()
    user_id = user["user_id"]
    # 2. Deposit 100 into that user's account
    response = api.post(f"/users/{user_id}/transactions",
                        data={"type": "DEPOSIT", "amount": 100})
    assert response.status == 201
    # 3. Check the balance went up
    balance = api.get(f"/users/{user_id}").json()["balance"]
    assert balance == 100
    response = api.post(f"/users/{user_id}/transactions",
                            data={"type": "WITHDRAW", "amount": 200})
    assert response.status == 400
    assert response.json()["detail"] == "Insufficient balance"
    balance = api.get(f"/users/{user_id}").json()["balance"]
    assert balance == 100