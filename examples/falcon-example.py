import json
from decimal import Decimal

from falcon import Request, Response, API, HTTP_200
from wsgiref import simple_server
from qval import qval, validate, Validator, QvalValidationError
from qval.framework_integration import setup_falcon_error_handlers

app = API()

# Setup the exception handlers
setup_falcon_error_handlers(app)


class DivisionResource(object):
    def on_get(self, req: Request, resp: Response):
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
            validate(req, a=int, b=int)
            # `b` must be anything but zero
            .nonzero("b")
        )
        with params as p:
            resp.status = HTTP_200
            resp.body = json.dumps({"answer": p.a // p.b})


class ExponentiationResource(object):
    @qval({"a": float, "b": float})
    def on_get(self, req: Request, resp: Response, params):
        """
        GET /api/pow?
        param a : float
        param b : float

        Example: GET /api/pow?a=2&b=3 -> 200, {"answer": 8.0}
        Example: GET /api/pow?a=2&b=3000000000000 -> 500,
        {
            "error": "An error has occurred while processing you request. Please contact the website administrator."
        }
        """
        # Here we don't catch the OverflowError if `b` is too big.
        # This will result in the 500 error on the client side.
        resp.status = HTTP_200
        resp.body = json.dumps({"answer": params.a ** params.b})


class PurchaseResource(object):
    @staticmethod
    def price_validator(price: int) -> bool:
        """
        A predicate to validate the `price` query parameter.
        Provides a custom error message.
        """
        if price <= 0:
            # If price does not match our requirements, we raise QvalValidationError() with a custom message.
            # This exception will be handled in the context manager and will be reraised
            # as InvalidQueryParamException() [HTTP 400].
            raise QvalValidationError(
                f"Price must be greater than zero, got '{price}'."
            )
        return True

    purchase_factories = {"price": Decimal, "item_id": int, "token": None}
    purchase_validators = {
        "token": Validator(lambda x: len(x) == 12),
        # Validator(p) can be omitted if there is only one predicate:
        "item_id": lambda x: x >= 0,
        # Access the underlying function without the get/set protocol.
        # In order to avoid this hack, define validators outside of the class.
        "price": price_validator.__func__,
    }

    @qval(purchase_factories, purchase_validators)
    def on_get(self, req: Request, resp: Response, params):
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
        resp.status = HTTP_200
        resp.body = json.dumps(
            {
                "success": f"Item '{params.item_id}' has been purchased. Check: {round(cost, 2)}$."
            }
        )


division = DivisionResource()
exponentiation = ExponentiationResource()
purchase = PurchaseResource()

app.add_route("/api/divide", division)
app.add_route("/api/pow", exponentiation)
app.add_route("/api/purchase", purchase)


if __name__ == "__main__":
    httpd = simple_server.make_server("127.0.0.1", 8000, app)
    httpd.serve_forever()
