from decimal import Decimal
from flask import Flask, request, jsonify
from qval import validate, qval_curry, Validator, QvalValidationError
from qval.framework_integration import setup_flask_error_handlers

app = Flask(__name__)

# Flask uses one global request object.
# You can automatically provide it to the `@qval()` decorator on each call
# by re-assigning `qval` with `qval_curry(request)`.
qval = qval_curry(request)

# Setup the exception handlers
setup_flask_error_handlers(app)


@app.route("/api/divide")
def division_view():
    """
    GET /api/divide?
    param a : int
    param b : int, nonzero

    Example: GET /api/divide?a=10&b=2&token=abcdefghijkl -> 200, {"answer": 5}
    """
    # Parameter validation occurs in the context manager.
    # If validation fails or user code throws an error, the context manager
    # will raise InvalidQueryParamException or APIException respectively.
    # In Django, these exception will be processed and result
    # in the error codes 400 and 500 on the client side.
    params = (
        validate(request, a=int, b=int)
        # `b` must be anything but zero
        .nonzero("b")
    )
    with params as p:
        return jsonify({"answer": p.a // p.b})


@app.route("/api/pow")
@qval({"a": float, "b": float})
def exponentiation_view(request, params):
    """
    Note that the `request` parameter is now being provided to the view.

    GET /api/pow?
    param a : float
    param b : float

    Example: GET /api/pow?a=2&b=3 -> 200, {"answer": 8.0}
    Example: GET /api/pow?a=2&b=3000000000000 -> 500,
    {
        "error": "An error occurred while processing you request. Please contact the website administrator."
    }
   """
    # Here we don't catch the OverflowError if `b` is too big.
    # This will result in the 500 error on the client side.
    return jsonify({"answer": params.a ** params.b})


def price_validator(price: int) -> bool:
    """
    A predicate to validate the `price` query parameter.
    Provides a custom error message.
    """
    if price <= 0:
        # If price does not match our requirements, we raise QvalValidationError() with a custom message.
        # This exception will be handled in the context manager and will be reraised
        # as InvalidQueryParamException() [HTTP 400].
        raise QvalValidationError(f"Price must be greater than zero, got '{price}'.")
    return True


purchase_factories = {"price": Decimal, "item_id": int, "token": None}
purchase_validators = {
    "token": Validator(lambda x: len(x) == 12),
    # Validator(p) can be omitted if there is only one predicate:
    "item_id": lambda x: x >= 0,
    "price": price_validator,
}


@app.route("/api/purchase")
@qval(purchase_factories, purchase_validators)
def purchase_view(request, params):
    """
    GET /api/purchase?
    param item_id : int, positive
    param price   : float, greater than zero
    param token   : string, length == 12

    Example: GET /api/purchase?item_id=1&price=5.8&token=abcdefghijkl
             -> {"success": "Item '1' has been purchased. Check: 5.92$."
    """
    tax = 0.02
    cost = params.price * Decimal(1 + tax)
    return jsonify(
        {
            "success": f"Item '{params.item_id}' has been purchased. Check: {round(cost, 2)}$."
        }
    )
