import secrets
from datetime import datetime

class PaymentGatewayProvider:
    """Base class for payment gateway integrations."""
    def process_charge(self, amount, currency="USD", description=""):
        raise NotImplementedError

class MockPaymentGateway(PaymentGatewayProvider):
    """A simulated payment gateway for development and sandbox environments."""
    def process_charge(self, amount, currency="USD", description=""):
        # Simulate successful transaction
        return {
            "status": "success",
            "transaction_id": f"SIM-{secrets.token_hex(8).upper()}",
            "amount": amount,
            "currency": currency,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Gateway Factory
def get_payment_gateway(provider_type="mock"):
    if provider_type == "mock":
        return MockPaymentGateway()
    # Add other providers here (e.g., Stripe, PayPal)
    raise ValueError(f"Unsupported payment provider: {provider_type}")
