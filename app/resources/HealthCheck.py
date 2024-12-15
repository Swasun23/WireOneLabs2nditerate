import falcon

class HealthCheckResource:
    def on_get(self, req, resp):
        """Health check endpoint."""
        resp.media = {"status": "ok"}
        resp.status = falcon.HTTP_200
