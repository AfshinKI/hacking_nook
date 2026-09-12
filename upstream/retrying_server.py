"""Local epd-server adapter: retry transient generation failures without new artwork."""
import logging
from epd_server import DisplayServer as BaseDisplayServer

LOG = logging.getLogger("nookpanel.generation")


class DisplayServer(BaseDisplayServer):
    def regenerate(self, only=None, force_refresh=False):
        # Serial upstream calls preserve its rendering lock and atomic PNG writes.
        # Three attempts per scheduled run; no concurrent Chromium retries.
        for attempt in range(3):
            try:
                return super().regenerate(only=only, force_refresh=force_refresh or attempt > 0)
            except Exception:
                if attempt == 2:
                    LOG.exception("Generation failed after 3 attempts; keeping existing images")
                    raise
                delay = 30 * (attempt + 1)
                LOG.exception("Generation failed; retrying in %d seconds (attempt %d/3)", delay, attempt + 2)
                if self.shutdown_event.wait(delay):
                    raise
