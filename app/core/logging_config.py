import logging
import sys
from app.core.config import settings

# HIPAA Safe Harbor — these fragments must never appear in log output
_PHI_FRAGMENTS = {
    "patient_name", "first_name", "last_name", "dob", "date_of_birth",
    "ssn", "social_security", "mrn", "member_id", "phone", "address",
    "email", "zip", "diagnosis", "icd",
}


class PHISafeFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage().lower()
        for fragment in _PHI_FRAGMENTS:
            if fragment in msg:
                record.msg = "[PHI-SCRUBBED] Log contained potential PHI — check logging call at %s:%s"
                record.args = (record.pathname, record.lineno)
                break
        return True


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger().addFilter(PHISafeFilter())
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
