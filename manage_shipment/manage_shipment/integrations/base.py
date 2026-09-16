class CourierAdapter:
    """Base interface for courier integrations."""

    provider = None

    def __init__(self, provider_doc=None):
        self.provider_doc = provider_doc

    def track(self, tracking_id, doc=None):
        raise NotImplementedError
