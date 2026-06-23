from . import domain
from ..ledger import application as ledger_application


def run(customer, amount=0):
    value = domain.first(customer)
    posted = ledger_application.posting(value)
    return posted + amount
