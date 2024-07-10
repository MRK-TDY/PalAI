import sentry_sdk

def log_additional_data(key: str, value: str):
    try:
        sentry_sdk.api.get_current_span().set_data(key, value)
    except:
        pass
