"""Runtime persistence facade; SQL lives here, never in HTTP or graph nodes."""
from backend.application.persistence.business import Business
from backend.application.persistence.commands import Commands
from backend.application.persistence.editorial import Editorial
from backend.application.persistence.exporting import Exporting
from backend.application.persistence.outputs import Outputs
from backend.application.persistence.queue import Queue
from backend.application.persistence.reads import Reads
from backend.application.persistence.session import Session


class RuntimeStore(Business, Commands, Editorial, Exporting, Outputs, Queue, Reads, Session):
    pass
