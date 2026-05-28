import requests
from models import Webhook

def send_notification(message, franchise_id=None):
    """
    Sends a notification to associated webhooks.
    """
    # 1. Fetch relevant webhooks
    if franchise_id:
        webhooks = Webhook.query.filter((Webhook.franchise_id == franchise_id) | (Webhook.franchise_id == None)).all()
    else:
        webhooks = Webhook.query.filter_by(franchise_id=None).all()

    for hook in webhooks:
        try:
            if hook.service == 'Discord':
                requests.post(hook.url, json={"content": message})
            elif hook.service == 'Slack':
                requests.post(hook.url, json={"text": message})
        except Exception as e:
            print(f"Error sending webhook to {hook.url}: {e}")

if __name__ == "__main__":
    # Test (wont send without a real URL in DB)
    pass
